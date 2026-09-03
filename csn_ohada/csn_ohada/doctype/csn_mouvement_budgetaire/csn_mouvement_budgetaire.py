import frappe
from frappe import _
from frappe.model.document import Document


class CSNMouvementBudgetaire(Document):
	def before_insert(self):
		if not getattr(self.flags, "from_budget_engine", False):
			frappe.throw(_("Les mouvements budgétaires sont créés uniquement par le moteur budgétaire."))

	def on_trash(self):
		frappe.throw(_("Un mouvement budgétaire validé ne peut pas être supprimé."))
