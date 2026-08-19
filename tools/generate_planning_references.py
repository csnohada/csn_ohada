import json
from pathlib import Path


ROOT = Path("csn_ohada/csn_ohada/doctype")

PERMISSIONS = [
    {
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
    },
    {
        "role": "CSN Directeur Financier",
        "create": 1,
        "email": 1,
        "export": 1,
        "print": 1,
        "read": 1,
        "report": 1,
        "share": 1,
        "write": 1,
    },
    {
        "role": "CSN Gestionnaire PTBA",
        "create": 1,
        "email": 1,
        "export": 1,
        "print": 1,
        "read": 1,
        "report": 1,
        "write": 1,
    },
    {"role": "CSN Comptable", "read": 1, "report": 1, "export": 1},
    {"role": "CSN Auditeur Interne", "read": 1, "report": 1, "export": 1},
]


def scrub(value):
    return value.lower().replace(" ", "_").replace("-", "_")


def class_name(value):
    return "".join(character for character in value if character.isalnum())


def create_doctype(name, fields, title_field, search_fields, controller=None):
    folder = ROOT / scrub(name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "__init__.py").write_text("", encoding="utf-8")

    if controller is None:
        controller = (
            "from frappe.model.document import Document\n\n\n"
            f"class {class_name(name)}(Document):\n"
            "    pass\n"
        )

    (folder / f"{scrub(name)}.py").write_text(controller, encoding="utf-8")

    document = {
        "actions": [],
        "allow_rename": 0,
        "autoname": "field:code",
        "doctype": "DocType",
        "engine": "InnoDB",
        "field_order": [field["fieldname"] for field in fields],
        "fields": fields,
        "index_web_pages_for_search": 0,
        "links": [],
        "module": "CSN OHADA",
        "name": name,
        "naming_rule": "By fieldname",
        "permissions": PERMISSIONS,
        "quick_entry": 1,
        "search_fields": search_fields,
        "sort_field": "modified",
        "sort_order": "DESC",
        "states": [],
        "title_field": title_field,
        "track_changes": 1,
    }

    with (folder / f"{scrub(name)}.json").open("w", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=1)
        stream.write("\n")

    print(f"Créé: {name}")


create_doctype(
    "CSN Zone Intervention",
    [
        {
            "fieldname": "code",
            "fieldtype": "Data",
            "label": "Code",
            "reqd": 1,
            "unique": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "zone_name",
            "fieldtype": "Data",
            "label": "Zone d'intervention",
            "reqd": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "zone_type",
            "fieldtype": "Select",
            "label": "Type de zone",
            "options": "National\nProvince\nTerritoire\nVille\nCommune\nLocalité\nAxe d'intervention",
            "reqd": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "parent_zone",
            "fieldtype": "Link",
            "label": "Zone parente",
            "options": "CSN Zone Intervention",
        },
        {
            "fieldname": "province",
            "fieldtype": "Data",
            "label": "Province",
            "in_list_view": 1,
        },
        {
            "fieldname": "description",
            "fieldtype": "Small Text",
            "label": "Description",
        },
        {
            "fieldname": "disabled",
            "fieldtype": "Check",
            "label": "Désactivée",
            "default": "0",
            "in_list_view": 1,
        },
    ],
    "zone_name",
    "code,zone_name,zone_type,province",
    controller='''import frappe
from frappe import _
from frappe.model.document import Document


class CSNZoneIntervention(Document):
    def validate(self):
        if self.parent_zone and self.parent_zone == self.name:
            frappe.throw(_("Une zone ne peut pas être sa propre zone parente."))
''',
)

create_doctype(
    "CSN Convention Financement",
    [
        {
            "fieldname": "code",
            "fieldtype": "Data",
            "label": "Référence de la convention",
            "reqd": 1,
            "unique": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "convention_name",
            "fieldtype": "Data",
            "label": "Intitulé",
            "reqd": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "company",
            "fieldtype": "Link",
            "label": "Société",
            "options": "Company",
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
            "fieldname": "bailleur",
            "fieldtype": "Link",
            "label": "Bailleur",
            "options": "CSN Bailleur",
        },
        {
            "fieldname": "signature_date",
            "fieldtype": "Date",
            "label": "Date de signature",
        },
        {
            "fieldname": "start_date",
            "fieldtype": "Date",
            "label": "Date de début",
            "reqd": 1,
        },
        {
            "fieldname": "end_date",
            "fieldtype": "Date",
            "label": "Date de fin",
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
            "fieldname": "approved_amount",
            "fieldtype": "Currency",
            "label": "Montant approuvé",
            "options": "currency",
            "reqd": 1,
        },
        {
            "fieldname": "reporting_frequency",
            "fieldtype": "Select",
            "label": "Fréquence de rapportage",
            "options": "Mensuelle\nTrimestrielle\nSemestrielle\nAnnuelle\nSelon échéancier",
            "default": "Trimestrielle",
        },
        {
            "fieldname": "status",
            "fieldtype": "Select",
            "label": "Statut",
            "options": "Brouillon\nActive\nSuspendue\nClôturée\nAnnulée",
            "default": "Brouillon",
            "reqd": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "purpose",
            "fieldtype": "Text",
            "label": "Objet de la convention",
        },
        {
            "fieldname": "agreement_file",
            "fieldtype": "Attach",
            "label": "Convention signée",
        },
        {
            "fieldname": "disabled",
            "fieldtype": "Check",
            "label": "Désactivée",
            "default": "0",
        },
    ],
    "convention_name",
    "code,convention_name,bailleur,source_financement,status",
    controller='''import frappe
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
''',
)
