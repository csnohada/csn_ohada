import frappe
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
