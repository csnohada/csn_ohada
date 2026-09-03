import frappe
from frappe import _
from frappe.model.document import Document


class CSNUniteOrganisationnelle(Document):
    def validate(self):
        if self.parent_unit == self.name:
            frappe.throw(_("Une unité ne peut pas être son propre parent."))

        if self.parent_unit:
            parent_company = frappe.db.get_value(
                "CSN Unite Organisationnelle", self.parent_unit, "company"
            )
            if parent_company and parent_company != self.company:
                frappe.throw(_("L'unité parente doit appartenir à la même entité juridique."))

        if self.cost_center:
            cost_center_company = frappe.db.get_value("Cost Center", self.cost_center, "company")
            if cost_center_company != self.company:
                frappe.throw(_("Le centre de coûts doit appartenir à l'entité juridique sélectionnée."))
