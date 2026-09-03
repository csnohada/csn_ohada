from __future__ import annotations

from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


ZERO = Decimal("0")
Q = Decimal("0.0001")
SIGNS = {
	"Engagement": ("committed", 1),
	"Dégagement": ("committed", -1),
	"Liquidation": ("liquidated", 1),
	"Annulation liquidation": ("liquidated", -1),
	"Paiement": ("paid", 1),
	"Annulation paiement": ("paid", -1),
}


def money(value) -> Decimal:
	return Decimal(str(value or 0)).quantize(Q)


def budget_position(ptba_line: str) -> dict:
	line = frappe.db.get_value(
		"CSN Ligne PTBA", ptba_line, ["budget_amount", "currency", "ptba", "disabled"], as_dict=True
	)
	if not line:
		frappe.throw(_("Ligne budgétaire introuvable."))
	result = {"budget": money(line.budget_amount), "committed": ZERO, "liquidated": ZERO, "paid": ZERO}
	for row in frappe.get_all(
		"CSN Mouvement Budgetaire",
		filters={"ptba_line": ptba_line},
		fields=["movement_type", "amount"],
	):
		bucket, sign = SIGNS[row.movement_type]
		result[bucket] += money(row.amount) * sign
	result["available"] = result["budget"] - result["committed"]
	result["currency"] = line.currency
	return result


def validate_engagement(doc) -> None:
	if money(doc.committed_amount) <= ZERO:
		frappe.throw(_("Le montant engagé doit être strictement positif."))
	request = frappe.get_doc("CSN Demande Depense", doc.expense_request)
	if request.docstatus != 1:
		frappe.throw(_("La demande de dépense doit être approuvée avant engagement."))
	if request.ptba_line != doc.ptba_line or request.company != doc.company or request.currency != doc.currency:
		frappe.throw(_("L'engagement doit reprendre la ligne, l'entité et la devise de la demande."))
	if money(doc.committed_amount) > money(request.requested_amount):
		frappe.throw(_("L'engagement ne peut pas dépasser le montant approuvé de la demande."))
	if doc.supplier:
		status = frappe.db.get_value("Supplier", doc.supplier, "csn_validation_status")
		if status != "Validé":
			frappe.throw(_("Le fournisseur doit être validé avant l'engagement."))
	position = budget_position(doc.ptba_line)
	doc.available_before = position["available"]
	doc.available_after = position["available"] - money(doc.committed_amount)
	if doc.available_after < ZERO:
		frappe.throw(
			_("Crédit insuffisant : disponible {0}, engagement demandé {1}.").format(
				position["available"], money(doc.committed_amount)
			)
		)


def _movement_exists(reference_doctype: str, reference_name: str, movement_type: str) -> bool:
	return bool(
		frappe.db.exists(
			"CSN Mouvement Budgetaire",
			{
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"movement_type": movement_type,
			},
		)
	)


def post_movement(*, line: str, movement_type: str, amount, currency: str, reference_doctype: str, reference_name: str, engagement: str | None = None, remarks: str | None = None) -> str:
	if movement_type not in SIGNS:
		frappe.throw(_("Type de mouvement budgétaire invalide."))
	if _movement_exists(reference_doctype, reference_name, movement_type):
		frappe.throw(_("Ce mouvement budgétaire a déjà été comptabilisé."))
	doc = frappe.get_doc(
		{
			"doctype": "CSN Mouvement Budgetaire",
			"naming_series": "MB-.YYYY.-.######",
			"posting_date": nowdate(),
			"company": frappe.db.get_value("CSN PTBA", frappe.db.get_value("CSN Ligne PTBA", line, "ptba"), "company"),
			"ptba_line": line,
			"movement_type": movement_type,
			"amount": money(amount),
			"currency": currency,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"engagement": engagement,
			"remarks": remarks,
		}
	)
	doc.flags.from_budget_engine = True
	doc.insert(ignore_permissions=True)
	_update_ptba_line_totals(line)
	return doc.name


def _update_ptba_line_totals(ptba_line: str) -> None:
	position = budget_position(ptba_line)
	frappe.db.set_value(
		"CSN Ligne PTBA",
		ptba_line,
		{
			"csn_committed_amount": position["committed"],
			"csn_liquidated_amount": position["liquidated"],
			"csn_paid_amount": position["paid"],
			"csn_available_amount": position["available"],
		},
		update_modified=False,
	)


def post_engagement(doc) -> None:
	post_movement(
		line=doc.ptba_line, movement_type="Engagement", amount=doc.committed_amount,
		currency=doc.currency, reference_doctype=doc.doctype, reference_name=doc.name, engagement=doc.name,
	)
	doc.db_set("status", "Engagé", update_modified=False)
	frappe.db.set_value("CSN Demande Depense", doc.expense_request, "status", "Engagée", update_modified=False)


def cancel_engagement(doc) -> None:
	position = engagement_position(doc.name)
	if position["liquidated"] > ZERO or position["paid"] > ZERO:
		frappe.throw(_("Un engagement liquidé ou payé ne peut pas être annulé."))
	post_movement(
		line=doc.ptba_line, movement_type="Dégagement", amount=doc.committed_amount,
		currency=doc.currency, reference_doctype=doc.doctype, reference_name=doc.name, engagement=doc.name,
		remarks=_("Annulation de l'engagement"),
	)
	doc.db_set("status", "Annulé", update_modified=False)


def engagement_position(engagement: str) -> dict:
	result = {"committed": ZERO, "liquidated": ZERO, "paid": ZERO}
	for row in frappe.get_all(
		"CSN Mouvement Budgetaire", filters={"engagement": engagement}, fields=["movement_type", "amount"]
	):
		bucket, sign = SIGNS[row.movement_type]
		result[bucket] += money(row.amount) * sign
	return result


def validate_purchase_order(doc, method=None) -> None:
	if not doc.csn_engagement:
		return
	engagement = frappe.get_doc("CSN Engagement Budgetaire", doc.csn_engagement)
	if engagement.docstatus != 1 or engagement.status == "Annulé":
		frappe.throw(_("L'engagement budgétaire doit être validé."))
	if engagement.company != doc.company or engagement.currency != doc.currency:
		frappe.throw(_("Le bon de commande doit avoir la même entité et la même devise que l'engagement."))
	if engagement.supplier and engagement.supplier != doc.supplier:
		frappe.throw(_("Le fournisseur ne correspond pas à celui de l'engagement."))
	if money(doc.grand_total) > money(engagement.committed_amount):
		frappe.throw(_("Le bon de commande dépasse l'engagement budgétaire."))


def validate_purchase_invoice(doc, method=None) -> None:
	if not doc.csn_engagement:
		return
	engagement = frappe.get_doc("CSN Engagement Budgetaire", doc.csn_engagement)
	position = engagement_position(engagement.name)
	remaining = position["committed"] - position["liquidated"]
	if engagement.company != doc.company or engagement.currency != doc.currency:
		frappe.throw(_("La facture doit avoir la même entité et la même devise que l'engagement."))
	if engagement.supplier and engagement.supplier != doc.supplier:
		frappe.throw(_("Le fournisseur de la facture ne correspond pas à l'engagement."))
	if doc.docstatus == 0 and money(doc.grand_total) > remaining:
		frappe.throw(_("La facture dépasse le solde non liquidé de l'engagement ({0}).").format(remaining))


def post_purchase_invoice(doc, method=None) -> None:
	if not doc.csn_engagement:
		return
	engagement = frappe.get_doc("CSN Engagement Budgetaire", doc.csn_engagement)
	post_movement(line=engagement.ptba_line, movement_type="Liquidation", amount=doc.grand_total, currency=doc.currency, reference_doctype=doc.doctype, reference_name=doc.name, engagement=engagement.name)
	_update_engagement_status(engagement.name)


def cancel_purchase_invoice(doc, method=None) -> None:
	if not doc.csn_engagement:
		return
	engagement = frappe.get_doc("CSN Engagement Budgetaire", doc.csn_engagement)
	post_movement(line=engagement.ptba_line, movement_type="Annulation liquidation", amount=doc.grand_total, currency=doc.currency, reference_doctype=doc.doctype, reference_name=doc.name, engagement=engagement.name)
	_update_engagement_status(engagement.name)


def validate_payment_entry(doc, method=None) -> None:
	if not doc.csn_engagement:
		return
	engagement = frappe.get_doc("CSN Engagement Budgetaire", doc.csn_engagement)
	position = engagement_position(engagement.name)
	remaining = position["liquidated"] - position["paid"]
	if doc.company != engagement.company:
		frappe.throw(_("Le paiement doit appartenir à la même entité que l'engagement."))
	if doc.payment_type != "Pay":
		frappe.throw(_("Seuls les décaissements peuvent être liés à un engagement."))
	if doc.docstatus == 0 and money(doc.paid_amount) > remaining:
		frappe.throw(_("Le paiement dépasse le montant liquidé restant ({0}).").format(remaining))


def post_payment_entry(doc, method=None) -> None:
	if not doc.csn_engagement:
		return
	engagement = frappe.get_doc("CSN Engagement Budgetaire", doc.csn_engagement)
	post_movement(line=engagement.ptba_line, movement_type="Paiement", amount=doc.paid_amount, currency=engagement.currency, reference_doctype=doc.doctype, reference_name=doc.name, engagement=engagement.name)
	_update_engagement_status(engagement.name)


def cancel_payment_entry(doc, method=None) -> None:
	if not doc.csn_engagement:
		return
	engagement = frappe.get_doc("CSN Engagement Budgetaire", doc.csn_engagement)
	post_movement(line=engagement.ptba_line, movement_type="Annulation paiement", amount=doc.paid_amount, currency=engagement.currency, reference_doctype=doc.doctype, reference_name=doc.name, engagement=engagement.name)
	_update_engagement_status(engagement.name)


def _update_engagement_status(name: str) -> None:
	position = engagement_position(name)
	if position["paid"] >= position["committed"]:
		status = "Payé"
	elif position["paid"] > ZERO:
		status = "Partiellement payé"
	elif position["liquidated"] >= position["committed"]:
		status = "Liquidé"
	elif position["liquidated"] > ZERO:
		status = "Partiellement liquidé"
	else:
		status = "Engagé"
	frappe.db.set_value("CSN Engagement Budgetaire", name, "status", status, update_modified=False)


def validate_supplier(doc, method=None) -> None:
	previous = doc.get_db_value("csn_validation_status") if not doc.is_new() else None
	if doc.csn_validation_status == "Validé" and previous != "Validé":
		if not doc.csn_legal_documents:
			frappe.throw(_("Le dossier légal est obligatoire pour valider un fournisseur."))
		if not set(frappe.get_roles()).intersection({"System Manager", "CSN Responsable Achats", "CSN Directeur Financier"}):
			frappe.throw(_("Vous n'êtes pas autorisé à valider un fournisseur."), frappe.PermissionError)
		doc.csn_validated_by = frappe.session.user
		doc.csn_validation_date = frappe.utils.now()


@frappe.whitelist()
def get_budget_position(ptba_line: str) -> dict:
	if not frappe.has_permission("CSN Ligne PTBA", "read"):
		frappe.throw(_("Accès refusé."), frappe.PermissionError)
	return {key: float(value) if isinstance(value, Decimal) else value for key, value in budget_position(ptba_line).items()}
