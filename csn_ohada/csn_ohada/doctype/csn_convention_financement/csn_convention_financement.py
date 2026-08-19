import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class CSNConventionFinancement(Document):
    def validate(self):
        if self.start_date and self.end_date:
            if getdate(self.end_date) < getdate(self.start_date):
                frappe.throw(_("La date de fin doit être postérieure à la date de début."))

        if flt(self.approved_amount) <= 0:
            frappe.throw(_("Le montant approuvé doit être strictement positif."))

        if self.source_financement:
            requires_donor = frappe.db.get_value(
                "CSN Source Financement",
                self.source_financement,
                "requires_donor",
            )
            if requires_donor and not self.bailleur:
                frappe.throw(
                    _("Un bailleur est obligatoire pour cette source de financement.")
                )
