from __future__ import annotations

from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import flt, getdate, now


Q = Decimal("0.0001")


def money(value) -> Decimal:
	return Decimal(str(value or 0)).quantize(Q)


def validate_treasury_account(doc) -> None:
	account = frappe.db.get_value(
		"Account", doc.account, ["company", "account_currency", "is_group", "disabled"], as_dict=True
	)
	if not account or account.company != doc.company:
		frappe.throw(_("Le compte comptable doit appartenir à l'entité juridique."))
	if account.is_group or account.disabled:
		frappe.throw(_("Le compte comptable doit être actif et imputable."))
	if account.account_currency != doc.currency:
		frappe.throw(_("La devise du compte de trésorerie doit correspondre à celle du compte comptable."))
	if money(doc.reconciliation_tolerance) < 0:
		frappe.throw(_("La tolérance de rapprochement ne peut pas être négative."))
	if doc.bank_account:
		bank = frappe.db.get_value("Bank Account", doc.bank_account, ["company", "account"], as_dict=True)
		if not bank or bank.company != doc.company or bank.account != doc.account:
			frappe.throw(_("Le compte bancaire ERPNext ne correspond pas au compte de trésorerie."))


def validate_treasury_operation(doc) -> None:
	if money(doc.gross_amount) <= 0 or money(doc.fee_amount) < 0:
		frappe.throw(_("Le montant brut doit être positif et les frais ne peuvent pas être négatifs."))
	if money(doc.fee_amount) > money(doc.gross_amount):
		frappe.throw(_("Les frais ne peuvent pas dépasser le montant brut."))
	doc.net_amount = money(doc.gross_amount) - money(doc.fee_amount)
	if flt(doc.exchange_rate) <= 0:
		frappe.throw(_("Le taux de change doit être strictement positif."))
	if doc.original_currency != doc.settlement_currency and (not doc.exchange_rate_source or not doc.exchange_rate_date):
		frappe.throw(_("La source et la date du taux sont obligatoires pour une opération multidevise."))
	doc.amount_cdf = money(doc.net_amount) * money(doc.exchange_rate)
	account = frappe.db.get_value(
		"CSN Compte Tresorerie", doc.treasury_account, ["company", "currency", "disabled"], as_dict=True
	)
	if not account or account.disabled or account.company != doc.company:
		frappe.throw(_("Compte de trésorerie invalide pour cette entité."))
	if account.currency != doc.settlement_currency:
		frappe.throw(_("La devise de règlement doit correspondre au compte de trésorerie."))


def cancel_treasury_operation(doc) -> None:
	if frappe.db.exists("CSN Rapprochement Tresorerie", {"treasury_operation": doc.name, "docstatus": 1}):
		frappe.throw(_("Une opération rapprochée ne peut pas être annulée."))
	doc.db_set("status", "Annulée", update_modified=False)


def validate_payment_treasury(doc, method=None) -> None:
	if not doc.csn_treasury_account:
		return
	account = frappe.db.get_value(
		"CSN Compte Tresorerie", doc.csn_treasury_account, ["company", "account", "currency", "disabled"], as_dict=True
	)
	if not account or account.disabled or account.company != doc.company:
		frappe.throw(_("Compte de trésorerie CSN invalide."))
	expected_account = doc.paid_from if doc.payment_type in ("Pay", "Internal Transfer") else doc.paid_to
	if expected_account != account.account:
		frappe.throw(_("Le compte ERPNext du paiement ne correspond pas au compte de trésorerie CSN."))
	if doc.paid_from_account_currency != doc.paid_to_account_currency:
		if not doc.csn_exchange_rate_source or not doc.csn_exchange_rate_date:
			frappe.throw(_("La source et la date du taux de change sont obligatoires."))
		if not doc.csn_exchange_rate_validated_by:
			doc.csn_exchange_rate_validated_by = frappe.session.user


def validate_reconciliation(doc) -> None:
	duplicate = frappe.db.exists(
		"CSN Rapprochement Tresorerie",
		{
			"name": ["!=", doc.name or ""],
			"docstatus": ["<", 2],
			"treasury_operation": doc.treasury_operation,
		},
	)
	if duplicate:
		frappe.throw(_("Cette opération possède déjà un rapprochement actif."))
	operation = frappe.get_doc("CSN Operation Tresorerie", doc.treasury_operation)
	payment = frappe.get_doc("Payment Entry", doc.payment_entry)
	if operation.docstatus != 1 or payment.docstatus != 1:
		frappe.throw(_("L'opération de trésorerie et le paiement doivent être validés."))
	if operation.status == "Rapprochée":
		frappe.throw(_("Cette opération de trésorerie est déjà rapprochée."))
	if operation.company != payment.company:
		frappe.throw(_("Les deux opérations doivent appartenir à la même entité juridique."))
	doc.currency = operation.settlement_currency
	doc.statement_amount = operation.net_amount
	doc.accounting_amount = payment.paid_amount if payment.payment_type in ("Pay", "Internal Transfer") else payment.received_amount
	doc.difference_amount = money(doc.statement_amount) - money(doc.accounting_amount)
	tolerance = money(frappe.db.get_value("CSN Compte Tresorerie", operation.treasury_account, "reconciliation_tolerance"))
	if abs(money(doc.difference_amount)) > tolerance and not doc.justification:
		frappe.throw(_("L'écart dépasse la tolérance; une justification est obligatoire."))
	if not doc.initiated_by:
		doc.initiated_by = frappe.session.user


def approve_reconciliation(doc) -> None:
	if doc.initiated_by == frappe.session.user:
		frappe.throw(_("L'initiateur ne peut pas approuver son propre rapprochement."))
	doc.approved_by = frappe.session.user
	doc.status = "Rapproché"


def post_reconciliation(doc) -> None:
	frappe.db.set_value(
		"CSN Operation Tresorerie", doc.treasury_operation,
		{"status": "Rapprochée", "payment_entry": doc.payment_entry}, update_modified=False,
	)


def cancel_reconciliation(doc) -> None:
	frappe.db.set_value(
		"CSN Operation Tresorerie", doc.treasury_operation,
		{"status": "Confirmée", "payment_entry": None}, update_modified=False,
	)
	doc.db_set("status", "Annulé", update_modified=False)
