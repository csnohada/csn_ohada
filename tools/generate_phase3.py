"""Generate Phase 3 budget execution DocTypes."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = ROOT / "csn_ohada" / "csn_ohada" / "doctype"


def f(name, kind, label, **kwargs):
	return {"fieldname": name, "fieldtype": kind, "label": label, **kwargs}


def perm(role, write=0, submit=0):
	row = {"role": role, "read": 1, "report": 1, "print": 1, "export": 1}
	if write:
		row.update({"create": 1, "write": 1})
	if submit:
		row.update({"submit": 1, "cancel": 1, "amend": 1})
	return row


ADMIN = {**perm("System Manager", 1, 1), "delete": 1, "share": 1, "email": 1}


def write(name, fields, controller, permissions, *, submittable=False, title=None, search=""):
	scrub = name.lower().replace(" ", "_")
	folder = DOCTYPE_ROOT / scrub
	folder.mkdir(parents=True, exist_ok=True)
	(folder / "__init__.py").touch()
	payload = {
		"actions": [], "allow_rename": 0, "autoname": "naming_series:", "doctype": "DocType",
		"engine": "InnoDB", "field_order": [x["fieldname"] for x in fields], "fields": fields,
		"index_web_pages_for_search": 0, "links": [], "module": "CSN OHADA", "name": name,
		"naming_rule": "By Naming Series", "permissions": permissions, "search_fields": search,
		"sort_field": "modified", "sort_order": "DESC", "states": [], "track_changes": 1,
	}
	if submittable:
		payload["is_submittable"] = 1
	if title:
		payload["title_field"] = title
	(folder / f"{scrub}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
	(folder / f"{scrub}.py").write_text(controller.strip() + "\n", encoding="utf-8")


write(
	"CSN Demande Depense",
	[
		f("naming_series", "Select", "Série", options="DD-.YYYY.-.#####", default="DD-.YYYY.-.#####", reqd=1),
		f("subject", "Data", "Objet de la dépense", reqd=1, in_list_view=1),
		f("company", "Link", "Entité juridique", options="Company", reqd=1),
		f("request_date", "Date", "Date de la demande", reqd=1, in_list_view=1),
		f("requester", "Link", "Demandeur", options="User", reqd=1),
		f("organisational_unit", "Link", "Unité organisationnelle", options="CSN Unite Organisationnelle", reqd=1),
		f("ptba_line", "Link", "Ligne budgétaire PTBA", options="CSN Ligne PTBA", reqd=1, in_list_view=1),
		f("supplier", "Link", "Fournisseur pressenti", options="Supplier"),
		f("currency", "Link", "Devise", options="Currency", reqd=1),
		f("requested_amount", "Currency", "Montant demandé", options="currency", reqd=1, in_list_view=1),
		f("purpose", "Text Editor", "Justification", reqd=1),
		f("supporting_document", "Attach", "Pièce justificative", reqd=1),
		f("status", "Select", "Statut", options="Brouillon\nSoumise\nApprouvée\nRejetée\nEngagée\nClôturée", default="Brouillon", read_only=1, in_list_view=1),
		f("amended_from", "Link", "Rectification de", options="CSN Demande Depense", read_only=1, no_copy=1),
	],
	'''import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CSNDemandeDepense(Document):
	def validate(self):
		if flt(self.requested_amount) <= 0:
			frappe.throw(_("Le montant demandé doit être strictement positif."))
		line = frappe.db.get_value("CSN Ligne PTBA", self.ptba_line, ["ptba", "currency", "disabled"], as_dict=True)
		if not line or line.disabled:
			frappe.throw(_("La ligne PTBA est introuvable ou désactivée."))
		ptba_company = frappe.db.get_value("CSN PTBA", line.ptba, "company")
		if ptba_company != self.company or line.currency != self.currency:
			frappe.throw(_("La ligne PTBA doit appartenir à la même entité et utiliser la même devise."))
		unit_company = frappe.db.get_value("CSN Unite Organisationnelle", self.organisational_unit, "company")
		if unit_company != self.company:
			frappe.throw(_("L'unité organisationnelle doit appartenir à l'entité de la demande."))

	def before_submit(self):
		if self.requester == frappe.session.user:
			frappe.throw(_("Le demandeur ne peut pas approuver seul sa propre demande."))
		self.status = "Approuvée"

	def on_cancel(self):
		if frappe.db.exists("CSN Engagement Budgetaire", {"expense_request": self.name, "docstatus": 1}):
			frappe.throw(_("Une demande engagée ne peut pas être annulée."))
		self.db_set("status", "Rejetée", update_modified=False)
''',
	[ADMIN, perm("CSN Demandeur", 1), perm("CSN Gestionnaire Budgetaire", 1, 1), perm("CSN Directeur Financier", 1, 1), perm("CSN Auditeur Interne")],
	submittable=True, title="subject", search="subject,requester,ptba_line,status",
)

write(
	"CSN Engagement Budgetaire",
	[
		f("naming_series", "Select", "Série", options="ENG-.YYYY.-.#####", default="ENG-.YYYY.-.#####", reqd=1),
		f("expense_request", "Link", "Demande de dépense", options="CSN Demande Depense", reqd=1, in_list_view=1),
		f("company", "Link", "Entité juridique", options="Company", reqd=1),
		f("engagement_date", "Date", "Date d'engagement", reqd=1, in_list_view=1),
		f("ptba_line", "Link", "Ligne budgétaire PTBA", options="CSN Ligne PTBA", reqd=1, in_list_view=1),
		f("supplier", "Link", "Fournisseur", options="Supplier"),
		f("currency", "Link", "Devise", options="Currency", reqd=1),
		f("exchange_rate", "Float", "Taux de change", default="1", reqd=1),
		f("committed_amount", "Currency", "Montant engagé", options="currency", reqd=1, in_list_view=1),
		f("available_before", "Currency", "Disponible avant engagement", options="currency", read_only=1),
		f("available_after", "Currency", "Disponible après engagement", options="currency", read_only=1),
		f("purchase_order", "Link", "Bon de commande", options="Purchase Order"),
		f("contract_reference", "Data", "Référence du contrat"),
		f("supporting_document", "Attach", "Pièce d'engagement", reqd=1),
		f("status", "Select", "Statut", options="Brouillon\nEngagé\nPartiellement liquidé\nLiquidé\nPartiellement payé\nPayé\nAnnulé", default="Brouillon", read_only=1, in_list_view=1),
		f("amended_from", "Link", "Rectification de", options="CSN Engagement Budgetaire", read_only=1, no_copy=1),
	],
	'''from frappe.model.document import Document


class CSNEngagementBudgetaire(Document):
	def validate(self):
		from csn_ohada.budget_engine import validate_engagement
		validate_engagement(self)

	def on_submit(self):
		from csn_ohada.budget_engine import post_engagement
		post_engagement(self)

	def on_cancel(self):
		from csn_ohada.budget_engine import cancel_engagement
		cancel_engagement(self)
''',
	[ADMIN, perm("CSN Gestionnaire Budgetaire", 1), perm("CSN Directeur Financier", 1, 1), perm("CSN Controleur Interne", 1, 1), perm("CSN Comptable"), perm("CSN Auditeur Interne")],
	submittable=True, title="expense_request", search="expense_request,ptba_line,supplier,status",
)

write(
	"CSN Mouvement Budgetaire",
	[
		f("naming_series", "Select", "Série", options="MB-.YYYY.-.######", default="MB-.YYYY.-.######", reqd=1),
		f("posting_date", "Date", "Date", reqd=1, in_list_view=1),
		f("company", "Link", "Entité juridique", options="Company", reqd=1),
		f("ptba_line", "Link", "Ligne budgétaire PTBA", options="CSN Ligne PTBA", reqd=1, in_list_view=1),
		f("movement_type", "Select", "Type", options="Engagement\nDégagement\nLiquidation\nAnnulation liquidation\nPaiement\nAnnulation paiement", reqd=1, in_list_view=1),
		f("amount", "Currency", "Montant", options="currency", reqd=1, in_list_view=1),
		f("currency", "Link", "Devise", options="Currency", reqd=1),
		f("reference_doctype", "Link", "Type de pièce", options="DocType", reqd=1),
		f("reference_name", "Dynamic Link", "Pièce", options="reference_doctype", reqd=1, in_list_view=1),
		f("engagement", "Link", "Engagement", options="CSN Engagement Budgetaire"),
		f("remarks", "Small Text", "Observations"),
	],
	'''import frappe
from frappe import _
from frappe.model.document import Document


class CSNMouvementBudgetaire(Document):
	def before_insert(self):
		if not getattr(self.flags, "from_budget_engine", False):
			frappe.throw(_("Les mouvements budgétaires sont créés uniquement par le moteur budgétaire."))

	def on_trash(self):
		frappe.throw(_("Un mouvement budgétaire validé ne peut pas être supprimé."))
''',
	[ADMIN, perm("CSN Gestionnaire Budgetaire"), perm("CSN Directeur Financier"), perm("CSN Comptable"), perm("CSN Auditeur Interne")],
	title="reference_name", search="ptba_line,movement_type,reference_name,engagement",
)

print("Phase 3 DocTypes generated.")
