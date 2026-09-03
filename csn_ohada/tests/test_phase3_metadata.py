import frappe
from frappe.tests import IntegrationTestCase


class TestPhase3Metadata(IntegrationTestCase):
	def test_budget_execution_doctypes_exist(self):
		for doctype in (
			"CSN Demande Depense",
			"CSN Engagement Budgetaire",
			"CSN Mouvement Budgetaire",
		):
			self.assertTrue(frappe.db.exists("DocType", doctype), doctype)

	def test_budget_movement_is_not_directly_writable(self):
		meta = frappe.get_meta("CSN Mouvement Budgetaire")
		for row in meta.permissions:
			if row.role != "System Manager":
				self.assertFalse(row.create)
				self.assertFalse(row.write)

	def test_erpnext_documents_have_budget_link(self):
		for doctype in ("Purchase Order", "Purchase Invoice", "Payment Entry"):
			self.assertTrue(frappe.get_meta(doctype).has_field("csn_engagement"), doctype)
