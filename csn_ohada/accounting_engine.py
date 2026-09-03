from __future__ import annotations

import hashlib
import json
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import getdate


ZERO = Decimal("0")
MONEY_QUANTUM = Decimal("0.0001")


def _decimal(value) -> Decimal:
	return Decimal(str(value or 0)).quantize(MONEY_QUANTUM)


def _active_primary_version() -> str | None:
	if not frappe.db.exists("DocType", "CSN Parametres Comptables"):
		return None
	return frappe.db.get_single_value("CSN Parametres Comptables", "primary_framework_version")


def _get_open_period(doc) -> str:
	if not doc.company or not doc.posting_date:
		frappe.throw(_("L'entité juridique et la date comptable sont obligatoires."))

	periods = frappe.get_all(
		"CSN Periode Comptable",
		filters={
			"company": doc.company,
			"start_date": ["<=", doc.posting_date],
			"end_date": [">=", doc.posting_date],
			"status": ["in", ("Ouverte", "Réouverte")],
		},
		pluck="name",
		limit=2,
	)
	if not periods:
		frappe.throw(_("Aucune période comptable ouverte ne couvre la date {0}.").format(doc.posting_date))
	if len(periods) > 1:
		frappe.throw(_("Plusieurs périodes ouvertes couvrent cette date. Corrigez le calendrier comptable."))
	if doc.csn_accounting_period and doc.csn_accounting_period != periods[0]:
		frappe.throw(_("La période sélectionnée ne correspond pas à la date comptable."))
	return periods[0]


def _validate_journal(doc) -> dict:
	if not doc.csn_journal:
		frappe.throw(_("Le journal comptable CSN est obligatoire."))
	journal = frappe.db.get_value(
		"CSN Journal Comptable",
		doc.csn_journal,
		["company", "disabled", "requires_supporting_document", "requires_review"],
		as_dict=True,
	)
	if not journal or journal.disabled:
		frappe.throw(_("Le journal comptable sélectionné est introuvable ou désactivé."))
	if journal.company != doc.company:
		frappe.throw(_("Le journal comptable doit appartenir à l'entité de l'écriture."))
	if journal.requires_supporting_document and not doc.csn_supporting_document:
		frappe.throw(_("Une pièce justificative principale est obligatoire pour ce journal."))
	return journal


def _validate_dimensions(row, account_reference: str | None) -> None:
	if not account_reference:
		return
	reference = frappe.db.get_value(
		"CSN Compte Referentiel",
		account_reference,
		[
			"requires_third_party",
			"requires_budget_line",
			"requires_project",
			"requires_fund",
			"requires_donor",
			"requires_campaign",
			"requires_emergency",
			"requires_cost_center",
			"requires_asset",
			"requires_inventory_item",
			"requires_bank_account",
			"status",
		],
		as_dict=True,
	)
	if not reference or reference.status != "Actif":
		frappe.throw(_("Le compte {0} n'est pas rattaché à un compte officiel actif.").format(row.account))

	requirements = {
		"requires_third_party": bool(row.party_type and row.party),
		"requires_budget_line": bool(row.csn_budget_line),
		"requires_project": bool(row.project),
		"requires_fund": bool(row.csn_fund_reference),
		"requires_donor": bool(row.csn_bailleur),
		"requires_campaign": bool(row.csn_campaign_reference),
		"requires_emergency": bool(row.csn_emergency_reference),
		"requires_cost_center": bool(row.cost_center),
		"requires_asset": bool(row.csn_asset),
		"requires_inventory_item": bool(row.csn_inventory_item),
		"requires_bank_account": bool(row.csn_bank_account),
	}
	missing = [key.removeprefix("requires_") for key, present in requirements.items() if reference.get(key) and not present]
	if missing:
		frappe.throw(
			_("Dimensions obligatoires manquantes sur le compte {0} : {1}").format(
				row.account, ", ".join(missing)
			)
		)


def _validate_lines(doc) -> tuple[Decimal, Decimal]:
	active_version = _active_primary_version()
	line_count = 0
	total_debit = ZERO
	total_credit = ZERO

	for row in doc.accounts:
		debit = _decimal(row.debit_in_account_currency)
		credit = _decimal(row.credit_in_account_currency)
		if debit < ZERO or credit < ZERO:
			frappe.throw(_("Les montants débit et crédit ne peuvent pas être négatifs."))
		if debit > ZERO and credit > ZERO:
			frappe.throw(_("Une ligne ne peut pas contenir simultanément un débit et un crédit."))
		if debit == ZERO and credit == ZERO:
			continue
		line_count += 1

		account = frappe.db.get_value(
			"Account",
			row.account,
			["company", "is_group", "disabled", "csn_account_reference"],
			as_dict=True,
		)
		if not account or account.company != doc.company:
			frappe.throw(_("Le compte {0} n'appartient pas à l'entité de l'écriture.").format(row.account))
		if account.is_group or account.disabled:
			frappe.throw(_("Le compte {0} n'est pas imputable ou est désactivé.").format(row.account))

		if active_version and not account.csn_account_reference:
			frappe.throw(_("Le compte {0} n'est pas rattaché au référentiel principal actif.").format(row.account))
		if row.csn_account_reference and row.csn_account_reference != account.csn_account_reference:
			frappe.throw(_("Le compte officiel de la ligne ne correspond pas au compte ERPNext."))
		row.csn_account_reference = account.csn_account_reference
		_validate_dimensions(row, account.csn_account_reference)

		total_debit += debit
		total_credit += credit

	if line_count < 2:
		frappe.throw(_("Une écriture doit contenir au moins deux lignes non nulles."))
	if total_debit != total_credit:
		frappe.throw(
			_("Écriture déséquilibrée : débit {0} et crédit {1}.").format(total_debit, total_credit)
		)
	if total_debit <= ZERO:
		frappe.throw(_("Le montant total de l'écriture doit être strictement positif."))
	return total_debit, total_credit


def validate_journal_entry(doc, method=None) -> None:
	if doc.docstatus == 2:
		return
	if not doc.csn_initiator:
		doc.csn_initiator = frappe.session.user
	doc.csn_accounting_period = _get_open_period(doc)
	_validate_journal(doc)
	if not doc.csn_source_operation:
		frappe.throw(_("L'opération métier d'origine est obligatoire."))
	if doc.csn_is_reversal and (not doc.csn_reversal_of or not doc.csn_reversal_reason):
		frappe.throw(_("L'écriture d'origine et la justification sont obligatoires pour une contre-passation."))
	_validate_lines(doc)


def before_submit_journal_entry(doc, method=None) -> None:
	journal = _validate_journal(doc)
	if journal.requires_review and doc.csn_initiator == frappe.session.user:
		frappe.throw(_("L'initiateur ne peut pas valider sa propre écriture."))
	doc.csn_validator = frappe.session.user


def _control_payload(doc) -> dict:
	return {
		"name": doc.name,
		"company": doc.company,
		"posting_date": str(doc.posting_date),
		"journal": doc.csn_journal,
		"period": doc.csn_accounting_period,
		"source_operation": doc.csn_source_operation,
		"supporting_document": doc.csn_supporting_document,
		"initiator": doc.csn_initiator,
		"validator": doc.csn_validator,
		"reversal_of": doc.csn_reversal_of,
		"lines": [
			{
				"account": row.account,
				"debit": str(_decimal(row.debit_in_account_currency)),
				"credit": str(_decimal(row.credit_in_account_currency)),
				"party_type": row.party_type,
				"party": row.party,
				"cost_center": row.cost_center,
				"project": row.project,
				"account_reference": row.csn_account_reference,
				"organisational_unit": row.csn_organisational_unit,
				"funding_source": row.csn_source_financement,
				"donor": row.csn_bailleur,
				"agreement": row.csn_convention,
				"zone": row.csn_zone_intervention,
				"budget_line": row.csn_budget_line,
				"fund": row.csn_fund_reference,
				"campaign": row.csn_campaign_reference,
				"emergency": row.csn_emergency_reference,
				"asset": row.csn_asset,
				"inventory_item": row.csn_inventory_item,
				"bank_account": row.csn_bank_account,
			}
			for row in doc.accounts
		],
	}


def on_submit_journal_entry(doc, method=None) -> None:
	payload = json.dumps(_control_payload(doc), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
	control_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
	frappe.db.set_value("Journal Entry", doc.name, "csn_control_hash", control_hash, update_modified=False)
	doc.csn_control_hash = control_hash

	if doc.csn_is_reversal and doc.csn_reversal_of:
		frappe.db.set_value(
			"Journal Entry", doc.csn_reversal_of, "csn_reversed_by", doc.name, update_modified=False
		)


def prevent_posted_entry_cancellation(doc, method=None) -> None:
	if not getattr(doc.flags, "csn_allow_cancel", False):
		frappe.throw(
			_("Une écriture comptabilisée est immuable. Créez une contre-passation ou une régularisation.")
		)


def validate_account_mapping(doc, method=None) -> None:
	if not doc.csn_account_reference:
		return
	reference = frappe.db.get_value(
		"CSN Compte Referentiel",
		doc.csn_account_reference,
		["framework_version", "status", "is_postable"],
		as_dict=True,
	)
	if not reference or reference.status != "Actif":
		frappe.throw(_("Le compte du référentiel doit être actif."))
	if not doc.is_group and not reference.is_postable:
		frappe.throw(_("Un compte ERPNext imputable ne peut pas être lié à un compte officiel non imputable."))
	active_version = _active_primary_version()
	if active_version and reference.framework_version != active_version:
		frappe.throw(_("Le compte doit être rattaché à la version principale active."))


@frappe.whitelist(methods=["POST"])
def create_reversal(
	journal_entry: str,
	posting_date: str,
	accounting_period: str,
	reversal_journal: str,
	reason: str,
) -> str:
	if not reason or not reason.strip():
		frappe.throw(_("La justification de la contre-passation est obligatoire."))
	original = frappe.get_doc("Journal Entry", journal_entry)
	if original.docstatus != 1:
		frappe.throw(_("Seule une écriture comptabilisée peut être contre-passée."))
	if original.csn_reversed_by:
		frappe.throw(_("Cette écriture a déjà été contre-passée par {0}.").format(original.csn_reversed_by))
	if not frappe.has_permission("Journal Entry", "create"):
		frappe.throw(_("Vous n'êtes pas autorisé à créer une contre-passation."), frappe.PermissionError)

	reversal = frappe.new_doc("Journal Entry")
	reversal.company = original.company
	reversal.posting_date = getdate(posting_date)
	reversal.voucher_type = original.voucher_type
	reversal.csn_journal = reversal_journal
	reversal.csn_accounting_period = accounting_period
	reversal.csn_source_operation = f"Contre-passation de {original.name}"
	reversal.csn_initiator = frappe.session.user
	reversal.csn_is_reversal = 1
	reversal.csn_reversal_of = original.name
	reversal.csn_reversal_reason = reason.strip()
	reversal.remark = _("Contre-passation de {0} : {1}").format(original.name, reason.strip())

	for source in original.accounts:
		target = reversal.append("accounts", {})
		for fieldname in (
			"account",
			"account_currency",
			"exchange_rate",
			"party_type",
			"party",
			"cost_center",
			"project",
			"reference_type",
			"reference_name",
			"csn_account_reference",
			"csn_organisational_unit",
			"csn_source_financement",
			"csn_bailleur",
			"csn_convention",
			"csn_zone_intervention",
			"csn_budget_line",
			"csn_fund_reference",
			"csn_campaign_reference",
			"csn_emergency_reference",
			"csn_asset",
			"csn_inventory_item",
			"csn_bank_account",
		):
			target.set(fieldname, source.get(fieldname))
		target.debit_in_account_currency = source.credit_in_account_currency
		target.credit_in_account_currency = source.debit_in_account_currency

	reversal.insert()
	return reversal.name


@frappe.whitelist(methods=["POST"])
def create_default_journals(company: str) -> list[str]:
	if not frappe.has_permission("CSN Journal Comptable", "create"):
		frappe.throw(_("Vous n'êtes pas autorisé à créer les journaux."), frappe.PermissionError)
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Entité juridique introuvable."))

	definitions = (
		("OD", "Opérations diverses", "Général"),
		("BQ", "Journal de banque", "Banque"),
		("CA", "Journal de caisse", "Caisse"),
		("AC", "Journal des achats", "Achats"),
		("VE", "Journal des ventes", "Ventes"),
		("PA", "Journal de paie", "Paie"),
		("AN", "À-nouveaux", "Ouverture"),
		("RG", "Régularisations", "Régularisation"),
		("EX", "Extournes", "Extourne"),
	)
	created = []
	for code, label, journal_type in definitions:
		if frappe.db.exists("CSN Journal Comptable", code):
			continue
		frappe.get_doc(
			{
				"doctype": "CSN Journal Comptable",
				"code": code,
				"journal_name": label,
				"company": company,
				"journal_type": journal_type,
				"naming_series": f"{code}-.YYYY.-.#####",
				"requires_supporting_document": 1,
				"requires_review": 1,
			}
		).insert()
		created.append(code)
	return created
