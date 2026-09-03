import frappe
from frappe.tests import IntegrationTestCase


class TestPhase2Metadata(IntegrationTestCase):
	def test_journal_entry_control_fields_exist(self):
		meta = frappe.get_meta("Journal Entry")
		for fieldname in (
			"csn_journal",
			"csn_accounting_period",
			"csn_source_operation",
			"csn_supporting_document",
			"csn_initiator",
			"csn_validator",
			"csn_control_hash",
			"csn_reversal_of",
		):
			self.assertTrue(meta.has_field(fieldname), fieldname)

	def test_accounting_reports_exist(self):
		for report in ("CSN Balance Generale", "CSN Grand Livre"):
			self.assertTrue(frappe.db.exists("Report", report), report)
