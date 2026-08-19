import frappe
from frappe import _
from frappe.model.document import Document


class CSNZoneIntervention(Document):
    def validate(self):
        if self.parent_zone and self.parent_zone == self.name:
            frappe.throw(_("Une zone ne peut pas être sa propre zone parente."))
