from frappe.model.document import Document


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
