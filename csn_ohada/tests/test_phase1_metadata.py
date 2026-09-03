import frappe
from frappe.tests import IntegrationTestCase


class TestPhase1Metadata(IntegrationTestCase):
	def test_account_reference_contains_required_import_fields(self):
		meta = frappe.get_meta("CSN Compte Referentiel")
		required = {
			"framework_version",
			"account_code",
			"account_label",
			"parent_account_code",
			"normal_balance",
			"is_postable",
			"requires_third_party",
			"requires_budget_line",
			"requires_project",
			"requires_fund",
			"requires_donor",
			"requires_campaign",
			"requires_emergency",
			"requires_cost_center",
			"requires_asset",
			"requires_inventory_item",
			"requires_bank_account",
			"valid_from",
			"valid_to",
			"legal_reference",
			"source_document",
			"status",
		}
		self.assertTrue(required.issubset({field.fieldname for field in meta.fields}))

	def test_accounting_settings_is_single(self):
		self.assertTrue(frappe.get_meta("CSN Parametres Comptables").issingle)

	def test_phase1_roles_exist(self):
		for role in (
			"CSN Administrateur Referentiel",
			"CSN Chef Comptabilite",
			"CSN Directeur Financier",
			"CSN Auditeur Interne",
			"CSN Administrateur Technique",
		):
			self.assertTrue(frappe.db.exists("Role", role), role)
