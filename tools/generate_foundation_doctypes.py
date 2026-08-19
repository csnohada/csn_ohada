import json
from pathlib import Path


ROOT = Path("csn_ohada/csn_ohada/doctype")
MODULE = "CSN OHADA"

FULL_PERMISSION = {
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

FINANCE_PERMISSION = {
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

READ_PERMISSIONS = [
    {"role": "CSN Comptable", "read": 1, "report": 1, "export": 1},
    {"role": "CSN Auditeur Interne", "read": 1, "report": 1, "export": 1},
    {"role": "CSN Gestionnaire PTBA", "read": 1, "report": 1},
]


DOCTYPES = {
    "CSN Secteur Humanitaire": {
        "autoname": "field:code",
        "title_field": "secteur_name",
        "search_fields": "code,secteur_name",
        "fields": [
            {
                "fieldname": "code",
                "fieldtype": "Data",
                "label": "Code",
                "reqd": 1,
                "unique": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "secteur_name",
                "fieldtype": "Data",
                "label": "Secteur humanitaire",
                "reqd": 1,
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
                "label": "Désactivé",
                "default": "0",
                "in_list_view": 1,
            },
        ],
    },
    "CSN Source Financement": {
        "autoname": "field:code",
        "title_field": "source_name",
        "search_fields": "code,source_name,source_type",
        "fields": [
            {
                "fieldname": "code",
                "fieldtype": "Data",
                "label": "Code",
                "reqd": 1,
                "unique": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "source_name",
                "fieldtype": "Data",
                "label": "Source de financement",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "source_type",
                "fieldtype": "Select",
                "label": "Type de source",
                "options": "Trésor public\nPartenaire technique et financier\nDon national\nRessources propres\nAutre",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "default_currency",
                "fieldtype": "Link",
                "label": "Devise habituelle",
                "options": "Currency",
                "reqd": 1,
            },
            {
                "fieldname": "requires_donor",
                "fieldtype": "Check",
                "label": "Bailleur obligatoire",
                "default": "0",
            },
            {
                "fieldname": "disabled",
                "fieldtype": "Check",
                "label": "Désactivée",
                "default": "0",
                "in_list_view": 1,
            },
        ],
    },
    "CSN Bailleur": {
        "autoname": "field:code",
        "title_field": "bailleur_name",
        "search_fields": "code,bailleur_name,bailleur_type",
        "fields": [
            {
                "fieldname": "code",
                "fieldtype": "Data",
                "label": "Code",
                "reqd": 1,
                "unique": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "bailleur_name",
                "fieldtype": "Data",
                "label": "Nom du bailleur",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "bailleur_type",
                "fieldtype": "Select",
                "label": "Type",
                "options": "État congolais\nInstitution publique\nOrganisation internationale\nAgence des Nations Unies\nONG\nEntreprise\nParticulier\nAutre",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "country",
                "fieldtype": "Link",
                "label": "Pays",
                "options": "Country",
            },
            {
                "fieldname": "tax_id",
                "fieldtype": "Data",
                "label": "Identifiant fiscal",
            },
            {
                "fieldname": "email",
                "fieldtype": "Data",
                "label": "Adresse électronique",
                "options": "Email",
            },
            {
                "fieldname": "phone",
                "fieldtype": "Data",
                "label": "Téléphone",
                "options": "Phone",
            },
            {
                "fieldname": "disabled",
                "fieldtype": "Check",
                "label": "Désactivé",
                "default": "0",
                "in_list_view": 1,
            },
        ],
    },
    "CSN EMO": {
        "autoname": "field:code",
        "title_field": "emo_name",
        "search_fields": "code,emo_name,emo_type,province",
        "fields": [
            {
                "fieldname": "code",
                "fieldtype": "Data",
                "label": "Code",
                "reqd": 1,
                "unique": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "emo_name",
                "fieldtype": "Data",
                "label": "Entité de mise en œuvre",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "emo_type",
                "fieldtype": "Select",
                "label": "Type d'EMO",
                "options": "Direction CSN-GHC\nService public\nAdministration provinciale\nONG\nPartenaire d'exécution\nAutre",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "province",
                "fieldtype": "Data",
                "label": "Province",
                "in_list_view": 1,
            },
            {
                "fieldname": "address",
                "fieldtype": "Small Text",
                "label": "Adresse",
            },
            {
                "fieldname": "contact_name",
                "fieldtype": "Data",
                "label": "Personne de contact",
            },
            {
                "fieldname": "contact_email",
                "fieldtype": "Data",
                "label": "Adresse électronique",
                "options": "Email",
            },
            {
                "fieldname": "contact_phone",
                "fieldtype": "Data",
                "label": "Téléphone",
                "options": "Phone",
            },
            {
                "fieldname": "has_dedicated_bank_account",
                "fieldtype": "Check",
                "label": "Dispose d'un compte bancaire dédié",
                "default": "0",
            },
            {
                "fieldname": "disabled",
                "fieldtype": "Check",
                "label": "Désactivée",
                "default": "0",
                "in_list_view": 1,
            },
        ],
    },
}


def scrub(value):
    return value.lower().replace(" ", "_").replace("-", "_")


def class_name(value):
    return "".join(character for character in value if character.isalnum())


def build_doctype(name, definition):
    folder = ROOT / scrub(name)
    folder.mkdir(parents=True, exist_ok=True)

    (folder / "__init__.py").write_text("", encoding="utf-8")

    controller = (
        "from frappe.model.document import Document\n\n\n"
        f"class {class_name(name)}(Document):\n"
        "    pass\n"
    )
    (folder / f"{scrub(name)}.py").write_text(controller, encoding="utf-8")

    fields = definition["fields"]
    document = {
        "actions": [],
        "allow_rename": 0,
        "autoname": definition["autoname"],
        "doctype": "DocType",
        "engine": "InnoDB",
        "field_order": [field["fieldname"] for field in fields],
        "fields": fields,
        "index_web_pages_for_search": 0,
        "links": [],
        "module": MODULE,
        "name": name,
        "naming_rule": "By fieldname",
        "permissions": [FULL_PERMISSION, FINANCE_PERMISSION, *READ_PERMISSIONS],
        "quick_entry": 1,
        "search_fields": definition["search_fields"],
        "sort_field": "modified",
        "sort_order": "DESC",
        "states": [],
        "title_field": definition["title_field"],
        "track_changes": 1,
    }

    with (folder / f"{scrub(name)}.json").open("w", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=1)
        stream.write("\n")


ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / "__init__.py").touch()

for doctype_name, doctype_definition in DOCTYPES.items():
    build_doctype(doctype_name, doctype_definition)
    print(f"Créé: {doctype_name}")
