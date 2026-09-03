import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class CSNVersionReferentielComptable(Document):
    def validate(self):
        if self.valid_to and getdate(self.valid_to) < getdate(self.valid_from):
            frappe.throw(_("La fin de validité ne peut pas précéder la prise d'effet."))

        if self.status in ("Approuvée", "Active"):
            required = (
                "framework_admin_validator",
                "finance_validator",
                "approving_authority",
                "approval_date",
                "legal_reference",
                "source_document",
            )
            missing = [self.meta.get_label(item) for item in required if not self.get(item)]
            if missing:
                frappe.throw(_("Activation impossible. Champs manquants : {0}").format(", ".join(missing)))

        if self.status == "Active":
            other = frappe.db.exists(
                "CSN Version Referentiel Comptable",
                {"framework": self.framework, "status": "Active", "name": ["!=", self.name or ""]},
            )
            if other:
                frappe.throw(_("Une seule version active est autorisée par référentiel."))

    def before_save(self):
        if self.source_document:
            file_url = frappe.db.get_value("File", {"file_url": self.source_document}, "name")
            if file_url:
                file_doc = frappe.get_doc("File", file_url)
                content = file_doc.get_content()
                if isinstance(content, str):
                    content = content.encode()
                self.source_checksum = hashlib.sha256(content).hexdigest()
