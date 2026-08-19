import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class CSNLignePTBA(Document):
    def validate(self):
        ptba = frappe.get_doc("CSN PTBA", self.ptba)

        if ptba.docstatus != 0:
            frappe.throw(_("Les lignes d'un PTBA soumis ne peuvent plus être modifiées."))

        duplicate = frappe.db.exists(
            "CSN Ligne PTBA",
            {
                "ptba": self.ptba,
                "line_code": self.line_code,
                "name": ["!=", self.name or ""],
            },
        )
        if duplicate:
            frappe.throw(_("Le code de ligne existe déjà dans ce PTBA."))

        if flt(self.quantity) <= 0 or flt(self.unit_cost) <= 0:
            frappe.throw(_("La quantité et le coût unitaire doivent être positifs."))

        self.budget_amount = flt(self.quantity) * flt(self.unit_cost)

        if self.currency != ptba.currency:
            frappe.throw(_("La devise de la ligne doit être celle du PTBA."))

        if self.start_date and getdate(self.start_date) < getdate(ptba.start_date):
            frappe.throw(_("L'activité commence avant l'exercice du PTBA."))

        if self.end_date and getdate(self.end_date) > getdate(ptba.end_date):
            frappe.throw(_("L'activité se termine après l'exercice du PTBA."))

        if getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(_("La date de fin doit être postérieure à la date de début."))

        account = frappe.db.get_value(
            "Account",
            self.budget_account,
            ["company", "root_type"],
            as_dict=True,
        )
        if not account or account.company != ptba.company:
            frappe.throw(_("Le compte budgétaire doit appartenir à la société du PTBA."))

        if account.root_type not in ("Expense", "Asset"):
            frappe.throw(_("Le compte budgétaire doit être un compte de charge ou d'actif."))

        cost_center_company = frappe.db.get_value(
            "Cost Center",
            self.cost_center,
            "company",
        )
        if cost_center_company != ptba.company:
            frappe.throw(_("Le centre de coûts doit appartenir à la société du PTBA."))

        if self.convention:
            convention = frappe.get_doc(
                "CSN Convention Financement",
                self.convention,
            )
            if convention.source_financement != self.source_financement:
                frappe.throw(
                    _("La convention et la ligne doivent avoir la même source de financement.")
                )

    def on_update(self):
        update_ptba_total(self.ptba)

    def on_trash(self):
        ptba_status = frappe.db.get_value("CSN PTBA", self.ptba, "docstatus")
        if ptba_status != 0:
            frappe.throw(_("Une ligne d'un PTBA soumis ne peut pas être supprimée."))

        update_ptba_total(self.ptba, exclude_name=self.name)


def update_ptba_total(ptba_name, exclude_name=None):
    filters = {"ptba": ptba_name, "disabled": 0}
    if exclude_name:
        filters["name"] = ["!=", exclude_name]

    total = sum(
        flt(value)
        for value in frappe.get_all(
            "CSN Ligne PTBA",
            filters=filters,
            pluck="budget_amount",
        )
    )

    frappe.db.set_value(
        "CSN PTBA",
        ptba_name,
        "total_budget",
        total,
        update_modified=False,
    )
