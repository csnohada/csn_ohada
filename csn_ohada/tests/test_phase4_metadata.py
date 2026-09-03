import frappe
from frappe.tests import IntegrationTestCase


class TestPhase4Metadata(IntegrationTestCase):
	def test_treasury_doctypes_exist(self):
		for doctype in (
			"CSN Compte Tresorerie",
			"CSN Operation Tresorerie",
			"CSN Rapprochement Tresorerie",
		):
			self.assertTrue(frappe.db.exists("DocType", doctype), doctype)

	def test_payment_entry_has_treasury_controls(self):
		meta = frappe.get_meta("Payment Entry")
		for fieldname in (
			"csn_treasury_account",
			"csn_payment_channel",
			"csn_exchange_rate_source",
			"csn_exchange_rate_date",
			"csn_exchange_rate_validated_by",
		):
			self.assertTrue(meta.has_field(fieldname), fieldname)
