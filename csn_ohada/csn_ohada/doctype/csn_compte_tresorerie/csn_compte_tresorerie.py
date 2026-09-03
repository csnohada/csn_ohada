from frappe.model.document import Document


class CSNCompteTresorerie(Document):
	def validate(self):
		from csn_ohada.treasury_engine import validate_treasury_account
		validate_treasury_account(self)
