import frappe
from frappe import _
from frappe.model.document import Document


class CSNJournalComptable(Document):
	def validate(self):
		for fieldname in ("default_debit_account", "default_credit_account"):
			account_name = self.get(fieldname)
			if not account_name:
				continue
			account = frappe.db.get_value(
				"Account", account_name, ["company", "is_group", "disabled"], as_dict=True
			)
			if not account or account.company != self.company:
				frappe.throw(_("Le compte par défaut doit appartenir à l'entité juridique du journal."))
			if account.is_group or account.disabled:
				frappe.throw(_("Le compte par défaut doit être imputable et actif."))
