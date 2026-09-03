from frappe.model.document import Document


class CSNRapprochementTresorerie(Document):
	def validate(self):
		from csn_ohada.treasury_engine import validate_reconciliation
		validate_reconciliation(self)

	def before_submit(self):
		from csn_ohada.treasury_engine import approve_reconciliation
		approve_reconciliation(self)

	def on_submit(self):
		from csn_ohada.treasury_engine import post_reconciliation
		post_reconciliation(self)

	def on_cancel(self):
		from csn_ohada.treasury_engine import cancel_reconciliation
		cancel_reconciliation(self)
