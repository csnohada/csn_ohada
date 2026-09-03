import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now


class CSNPeriodeComptable(Document):
    def validate(self):
        start = getdate(self.start_date)
        end = getdate(self.end_date)
        if end < start:
            frappe.throw(_("La date de fin doit être postérieure à la date de début."))

        fiscal_year = frappe.db.get_value(
            "Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True
        )
        if not fiscal_year or start < getdate(fiscal_year.year_start_date) or end > getdate(fiscal_year.year_end_date):
            frappe.throw(_("La période doit être comprise dans l'exercice fiscal."))

        overlap = frappe.db.sql(
            """
            select name from `tabCSN Periode Comptable`
            where company=%s and fiscal_year=%s and name!=%s
              and start_date <= %s and end_date >= %s
            limit 1
            """,
            (self.company, self.fiscal_year, self.name or "", end, start),
        )
        if overlap:
            frappe.throw(_("Cette période chevauche une période comptable existante."))

        previous_status = self.get_db_value("status") if not self.is_new() else None
        if previous_status == "Clôturée" and self.status == "Réouverte":
            if not self.reopening_reason:
                frappe.throw(_("Une justification est obligatoire pour rouvrir une période."))
            if not frappe.has_permission("CSN Periode Comptable", ptype="write"):
                frappe.throw(_("Vous n'êtes pas autorisé à rouvrir cette période."), frappe.PermissionError)
            self.reopened_by = frappe.session.user
            self.reopened_on = now()
        elif self.status == "Clôturée" and previous_status != "Clôturée":
            self.closed_by = frappe.session.user
            self.closed_on = now()
