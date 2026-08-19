import frappe


CSN_ROLES = (
    "CSN Demandeur",
    "CSN Réceptionniste",
    "CSN Gestionnaire PTBA",
    "CSN Comptable",
    "CSN Trésorier",
    "CSN Chef Comptabilité",
    "CSN Agent Fiscal",
    "CSN Directeur Financier",
    "CSN Directeur Général",
    "CSN Superviseur EMO",
    "CSN Auditeur Interne",
    "CSN Conseil Administration",
)

SECTEURS = (
    ("SANTE", "Santé"),
    ("NUTRITION", "Nutrition"),
    ("ABRI", "Abri"),
    ("SEC-ALIM", "Sécurité alimentaire"),
    ("EDUCATION", "Éducation"),
    ("LOGISTIQUE", "Logistique"),
    ("PROTECTION", "Protection"),
    ("EHA", "Eau, hygiène et assainissement"),
)

SOURCES = (
    ("TRESOR", "Trésor public", "Trésor public", "CDF", 0),
    (
        "PTF",
        "Partenaires techniques et financiers",
        "Partenaire technique et financier",
        "USD",
        1,
    ),
    ("DON-NAT", "Dons nationaux", "Don national", "CDF", 1),
    ("PROPRES", "Ressources propres CSN-GHC", "Ressources propres", "CDF", 0),
)


def ensure_roles():
    for role_name in CSN_ROLES:
        if frappe.db.exists("Role", role_name):
            continue

        frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
                "is_custom": 0,
                "disabled": 0,
            }
        ).insert(ignore_permissions=True)


def ensure_sectors():
    if not frappe.db.exists("DocType", "CSN Secteur Humanitaire"):
        return

    for code, secteur_name in SECTEURS:
        if frappe.db.exists("CSN Secteur Humanitaire", code):
            continue

        frappe.get_doc(
            {
                "doctype": "CSN Secteur Humanitaire",
                "code": code,
                "secteur_name": secteur_name,
                "disabled": 0,
            }
        ).insert(ignore_permissions=True)


def ensure_funding_sources():
    if not frappe.db.exists("DocType", "CSN Source Financement"):
        return

    for code, source_name, source_type, currency, requires_donor in SOURCES:
        if frappe.db.exists("CSN Source Financement", code):
            continue

        frappe.get_doc(
            {
                "doctype": "CSN Source Financement",
                "code": code,
                "source_name": source_name,
                "source_type": source_type,
                "default_currency": currency,
                "requires_donor": requires_donor,
                "disabled": 0,
            }
        ).insert(ignore_permissions=True)


def ensure_master_data():
    ensure_sectors()
    ensure_funding_sources()
    frappe.db.commit()


def after_install():
    ensure_roles()
    ensure_master_data()


def after_migrate():
    ensure_roles()
    ensure_master_data()
