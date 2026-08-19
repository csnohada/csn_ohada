import json
from pathlib import Path


ROOT = Path("csn_ohada/csn_ohada/doctype")


def permissions(submittable=False):
    manager = {
        "role": "System Manager",
        "create": 1,
        "delete": 1,
        "email": 1,
        "export": 1,
        "print": 1,
        "read": 1,
        "report": 1,
        "share": 1,
        "write": 1,
    }
    ptba = {
        "role": "CSN Gestionnaire PTBA",
        "create": 1,
        "email": 1,
        "export": 1,
        "print": 1,
        "read": 1,
        "report": 1,
        "write": 1,
    }
    finance = {
        "role": "CSN Directeur Financier",
        "create": 1,
        "email": 1,
        "export": 1,
        "print": 1,
        "read": 1,
        "report": 1,
        "share": 1,
        "write": 1,
    }

    if submittable:
        manager.update({"submit": 1, "cancel": 1, "amend": 1})
        finance.update({"submit": 1, "cancel": 1, "amend": 1})

    return [
        manager,
        ptba,
        finance,
        {"role": "CSN Directeur Général", "read": 1, "print": 1, "report": 1},
        {
            "role": "CSN Auditeur Interne",
            "read": 1,
            "print": 1,
            "report": 1,
            "export": 1,
        },
        {
            "role": "CSN Conseil Administration",
            "read": 1,
            "print": 1,
            "report": 1,
        },
    ]


def create_doctype(
    name,
    fields,
    controller,
    autoname,
    title_field,
    search_fields,
    submittable=False,
):
    scrubbed = name.lower().replace(" ", "_").replace("-", "_")
    folder = ROOT / scrubbed
    folder.mkdir(parents=True, exist_ok=True)

    (folder / "__init__.py").write_text("", encoding="utf-8")
    (folder / f"{scrubbed}.py").write_text(controller, encoding="utf-8")

    document = {
        "actions": [],
        "allow_rename": 0,
        "autoname": autoname,
        "doctype": "DocType",
        "engine": "InnoDB",
        "field_order": [field["fieldname"] for field in fields],
        "fields": fields,
        "index_web_pages_for_search": 0,
        "is_submittable": 1 if submittable else 0,
        "links": [],
        "module": "CSN OHADA",
        "name": name,
        "naming_rule": (
            "By Naming Series" if autoname == "naming_series:" else "By fieldname"
        ),
        "permissions": permissions(submittable),
        "search_fields": search_fields,
        "sort_field": "modified",
        "sort_order": "DESC",
        "states": [],
        "title_field": title_field,
        "track_changes": 1,
    }

    with (folder / f"{scrubbed}.json").open("w", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=1)
        stream.write("\n")

    print(f"Créé: {name}")


PTBA_FIELDS = [
    {
        "fieldname": "naming_series",
        "fieldtype": "Select",
        "label": "Série",
        "options": "PTBA-.YYYY.-.####",
        "default": "PTBA-.YYYY.-.####",
        "reqd": 1,
    },
    {
        "fieldname": "ptba_name",
        "fieldtype": "Data",
        "label": "Intitulé du PTBA",
        "reqd": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "company",
        "fieldtype": "Link",
        "label": "Société",
        "options": "Company",
        "reqd": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "fiscal_year",
        "fieldtype": "Link",
        "label": "Exercice fiscal",
        "options": "Fiscal Year",
        "reqd": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "version_number",
        "fieldtype": "Int",
        "label": "Version",
        "default": "1",
        "reqd": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "start_date",
        "fieldtype": "Date",
        "label": "Date de début",
        "read_only": 1,
    },
    {
        "fieldname": "end_date",
        "fieldtype": "Date",
        "label": "Date de fin",
        "read_only": 1,
    },
    {
        "fieldname": "currency",
        "fieldtype": "Link",
        "label": "Devise du PTBA",
        "options": "Currency",
        "reqd": 1,
    },
    {
        "fieldname": "total_budget",
        "fieldtype": "Currency",
        "label": "Budget total",
        "options": "currency",
        "read_only": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "orientation_note",
        "fieldtype": "Attach",
        "label": "Note d'orientation",
    },
    {
        "fieldname": "approval_minutes",
        "fieldtype": "Attach",
        "label": "Procès-verbal d'approbation",
    },
    {
        "fieldname": "description",
        "fieldtype": "Text Editor",
        "label": "Observations",
    },
    {
        "fieldname": "amended_from",
        "fieldtype": "Link",
        "label": "Rectification de",
        "options": "CSN PTBA",
        "no_copy": 1,
        "read_only": 1,
    },
]

PTBA_CONTROLLER = '''import frappe
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
'''

LINE_FIELDS = [
    {
        "fieldname": "naming_series",
        "fieldtype": "Select",
        "label": "Série",
        "options": "PTBA-LIG-.YYYY.-.#####",
        "default": "PTBA-LIG-.YYYY.-.#####",
        "reqd": 1,
    },
    {
        "fieldname": "ptba",
        "fieldtype": "Link",
        "label": "PTBA",
        "options": "CSN PTBA",
        "reqd": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "line_code",
        "fieldtype": "Data",
        "label": "Code de ligne",
        "reqd": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "activity_name",
        "fieldtype": "Data",
        "label": "Activité",
        "reqd": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "sector",
        "fieldtype": "Link",
        "label": "Secteur humanitaire",
        "options": "CSN Secteur Humanitaire",
        "reqd": 1,
    },
    {
        "fieldname": "emo",
        "fieldtype": "Link",
        "label": "Entité de mise en œuvre",
        "options": "CSN EMO",
        "reqd": 1,
    },
    {
        "fieldname": "zone",
        "fieldtype": "Link",
        "label": "Zone d'intervention",
        "options": "CSN Zone Intervention",
        "reqd": 1,
    },
    {
        "fieldname": "source_financement",
        "fieldtype": "Link",
        "label": "Source de financement",
        "options": "CSN Source Financement",
        "reqd": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "convention",
        "fieldtype": "Link",
        "label": "Convention",
        "options": "CSN Convention Financement",
    },
    {
        "fieldname": "budget_account",
        "fieldtype": "Link",
        "label": "Compte budgétaire OHADA",
        "options": "Account",
        "reqd": 1,
    },
    {
        "fieldname": "cost_center",
        "fieldtype": "Link",
        "label": "Centre de coûts",
        "options": "Cost Center",
        "reqd": 1,
    },
    {
        "fieldname": "start_date",
        "fieldtype": "Date",
        "label": "Début de l'activité",
        "reqd": 1,
    },
    {
        "fieldname": "end_date",
        "fieldtype": "Date",
        "label": "Fin de l'activité",
        "reqd": 1,
    },
    {
        "fieldname": "currency",
        "fieldtype": "Link",
        "label": "Devise",
        "options": "Currency",
        "reqd": 1,
    },
    {
        "fieldname": "quantity",
        "fieldtype": "Float",
        "label": "Quantité",
        "default": "1",
        "reqd": 1,
    },
    {
        "fieldname": "unit_cost",
        "fieldtype": "Currency",
        "label": "Coût unitaire",
        "options": "currency",
        "reqd": 1,
    },
    {
        "fieldname": "budget_amount",
        "fieldtype": "Currency",
        "label": "Montant budgété",
        "options": "currency",
        "read_only": 1,
        "in_list_view": 1,
    },
    {
        "fieldname": "justification",
        "fieldtype": "Small Text",
        "label": "Justification et hypothèses de coût",
    },
    {
        "fieldname": "disabled",
        "fieldtype": "Check",
        "label": "Désactivée",
        "default": "0",
    },
]

LINE_CONTROLLER = '''import frappe
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
'''

create_doctype(
    "CSN PTBA",
    PTBA_FIELDS,
    PTBA_CONTROLLER,
    "naming_series:",
    "ptba_name",
    "ptba_name,company,fiscal_year",
    submittable=True,
)

create_doctype(
    "CSN Ligne PTBA",
    LINE_FIELDS,
    LINE_CONTROLLER,
    "naming_series:",
    "activity_name",
    "line_code,activity_name,ptba,sector,emo",
)
