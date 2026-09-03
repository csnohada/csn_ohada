import frappe
from frappe import _
from frappe.model.document import Document


class CSNParametresComptables(Document):
    def validate(self):
        if self.enable_dual_reporting and not self.secondary_reporting_framework:
            frappe.throw(_("Le référentiel secondaire est obligatoire en mode dual reporting."))
        if self.secondary_reporting_framework == self.accounting_primary_framework:
            frappe.throw(_("Les référentiels principal et secondaire doivent être différents."))

        if self.primary_framework_version:
            version = frappe.db.get_value(
                "CSN Version Referentiel Comptable",
                self.primary_framework_version,
                ["framework", "status", "framework_admin_validator", "finance_validator", "approving_authority", "legal_reference", "source_document"],
                as_dict=True,
            )
            if not version or version.framework != self.accounting_primary_framework:
                frappe.throw(_("La version sélectionnée n'appartient pas au référentiel principal."))
            if version.status != "Active":
                frappe.throw(_("La version principale doit être active."))
            required = ("framework_admin_validator", "finance_validator", "approving_authority", "legal_reference", "source_document")
            if any(not version.get(item) for item in required):
                frappe.throw(_("Le référentiel principal ne satisfait pas le circuit de validation requis."))
