from frappe.model.document import Document


class CSNOperationTresorerie(Document):
	def validate(self):
		from csn_ohada.treasury_engine import validate_treasury_operation
		validate_treasury_operation(self)

	def before_submit(self):
		self.status = "Confirmée"

	def on_cancel(self):
		from csn_ohada.treasury_engine import cancel_treasury_operation
		cancel_treasury_operation(self)
