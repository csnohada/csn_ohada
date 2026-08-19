import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CSNPTBA(Document):
    def validate(self):
        self._set_fiscal_year_dates()

        if self.version_number < 1:
            frappe.throw(_("Le numéro de version doit être supérieur ou égal à 1."))

        self.total_budget = get_ptba_total(self.name)

    def before_submit(self):
        active_lines = frappe.db.count(
            "CSN Ligne PTBA",
            {"ptba": self.name, "disabled": 0},
        )
        if not active_lines:
            frappe.throw(_("Le PTBA doit contenir au moins une ligne budgétaire."))

        self.total_budget = get_ptba_total(self.name)
        if flt(self.total_budget) <= 0:
            frappe.throw(_("Le budget total du PTBA doit être strictement positif."))

    def _set_fiscal_year_dates(self):
        if not self.fiscal_year:
            return

        dates = frappe.db.get_value(
            "Fiscal Year",
            self.fiscal_year,
            ["year_start_date", "year_end_date"],
            as_dict=True,
        )
        if not dates:
            frappe.throw(_("Exercice fiscal introuvable."))

        self.start_date = dates.year_start_date
        self.end_date = dates.year_end_date


def get_ptba_total(ptba_name):
    if not ptba_name:
        return 0

    return sum(
        flt(value)
        for value in frappe.get_all(
            "CSN Ligne PTBA",
            filters={"ptba": ptba_name, "disabled": 0},
            pluck="budget_amount",
        )
    )
