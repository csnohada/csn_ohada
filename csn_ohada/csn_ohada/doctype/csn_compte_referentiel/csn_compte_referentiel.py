import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class CSNCompteReferentiel(Document):
    def autoname(self):
        self.code = f"{self.framework_version}::{self.account_code}"
        self.name = self.code

    def validate(self):
        if self.valid_to and getdate(self.valid_to) < getdate(self.valid_from):
            frappe.throw(_("La fin de validité ne peut pas précéder la date de début."))
        if self.parent_account_code == self.account_code:
            frappe.throw(_("Un compte ne peut pas être son propre parent."))

        version_status = frappe.db.get_value(
            "CSN Version Referentiel Comptable", self.framework_version, "status"
        )
        if version_status in ("Active", "Inactive") and self.has_value_changed("account_code"):
            frappe.throw(_("Les codes d'une version active ou historique sont immuables."))

        if self.parent_account_code:
            parent = frappe.db.exists(
                "CSN Compte Referentiel",
                {
                    "framework_version": self.framework_version,
                    "account_code": self.parent_account_code,
                },
            )
            if not parent:
                frappe.throw(_("Le compte parent n'existe pas dans cette version du référentiel."))

    def on_trash(self):
        if self.status in ("Actif", "Fermé"):
            frappe.throw(_("Un compte activé ou historique ne peut pas être supprimé."))
