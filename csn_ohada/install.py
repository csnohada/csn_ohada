import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


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
    "CSN President Conseil Administration",
    "CSN Direction Generale",
    "CSN Direction Generale Adjointe",
    "CSN Responsable Financier",
    "CSN Directeur Administratif Financier",
    "CSN Gestionnaire Budgetaire",
    "CSN Chef Comptabilite",
    "CSN Caissier",
    "CSN Controleur Interne",
    "CSN Responsable Achats",
    "CSN Responsable Logistique",
    "CSN Gestionnaire Stock",
    "CSN Gestionnaire Immobilisations",
    "CSN Responsable Projet",
    "CSN Responsable Antenne",
    "CSN Commissaire Comptes",
    "CSN Tutelle Lecture Seule",
    "CSN Auditeur Externe",
    "CSN Administrateur Technique",
    "CSN Administrateur Referentiel",
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


def ensure_finance_home():
    """Make the existing Finance workspace the default desk landing page."""
    workspace = "Finance CSN-GHC"
    if not frappe.db.exists("Workspace", workspace):
        return

    if frappe.get_meta("System Settings").has_field("default_app"):
        frappe.db.set_single_value("System Settings", "default_app", "csn_ohada")

    user_meta = frappe.get_meta("User")
    values = {}
    if user_meta.has_field("default_workspace"):
        values["default_workspace"] = workspace
    if user_meta.has_field("default_app"):
        values["default_app"] = "csn_ohada"
    if not values:
        return

    for user in frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        pluck="name",
    ):
        frappe.db.set_value("User", user, values, update_modified=False)


def ensure_accounting_custom_fields():
    custom_fields = {
        "Journal Entry": [
            {
                "fieldname": "csn_accounting_section",
                "fieldtype": "Section Break",
                "label": "Contrôle comptable CSN-GHC",
                "insert_after": "remark",
                "collapsible": 1,
            },
            {
                "fieldname": "csn_journal",
                "fieldtype": "Link",
                "label": "Journal comptable CSN",
                "options": "CSN Journal Comptable",
                "insert_after": "csn_accounting_section",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "csn_accounting_period",
                "fieldtype": "Link",
                "label": "Période comptable CSN",
                "options": "CSN Periode Comptable",
                "insert_after": "csn_journal",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "csn_source_operation",
                "fieldtype": "Data",
                "label": "Opération métier d'origine",
                "insert_after": "csn_accounting_period",
            },
            {
                "fieldname": "csn_supporting_document",
                "fieldtype": "Attach",
                "label": "Pièce justificative principale",
                "insert_after": "csn_source_operation",
            },
            {
                "fieldname": "csn_control_column",
                "fieldtype": "Column Break",
                "insert_after": "csn_supporting_document",
            },
            {
                "fieldname": "csn_initiator",
                "fieldtype": "Link",
                "label": "Initiateur",
                "options": "User",
                "read_only": 1,
                "no_copy": 1,
                "insert_after": "csn_control_column",
            },
            {
                "fieldname": "csn_validator",
                "fieldtype": "Link",
                "label": "Validateur",
                "options": "User",
                "read_only": 1,
                "no_copy": 1,
                "insert_after": "csn_initiator",
            },
            {
                "fieldname": "csn_control_hash",
                "fieldtype": "Data",
                "label": "Empreinte de contrôle SHA-256",
                "read_only": 1,
                "no_copy": 1,
                "insert_after": "csn_validator",
            },
            {
                "fieldname": "csn_reversal_section",
                "fieldtype": "Section Break",
                "label": "Contre-passation et extourne",
                "insert_after": "csn_control_hash",
                "collapsible": 1,
            },
            {
                "fieldname": "csn_is_reversal",
                "fieldtype": "Check",
                "label": "Écriture de contre-passation",
                "read_only": 1,
                "no_copy": 1,
                "insert_after": "csn_reversal_section",
            },
            {
                "fieldname": "csn_reversal_of",
                "fieldtype": "Link",
                "label": "Contre-passation de",
                "options": "Journal Entry",
                "read_only": 1,
                "no_copy": 1,
                "insert_after": "csn_is_reversal",
            },
            {
                "fieldname": "csn_reversal_reason",
                "fieldtype": "Small Text",
                "label": "Justification de la correction",
                "no_copy": 1,
                "insert_after": "csn_reversal_of",
            },
            {
                "fieldname": "csn_reversed_by",
                "fieldtype": "Link",
                "label": "Contre-passée par",
                "options": "Journal Entry",
                "read_only": 1,
                "no_copy": 1,
                "insert_after": "csn_reversal_reason",
            },
        ],
        "Journal Entry Account": [
            {
                "fieldname": "csn_dimensions_section",
                "fieldtype": "Section Break",
                "label": "Dimensions analytiques CSN-GHC",
                "insert_after": "reference_name",
                "collapsible": 1,
            },
            {
                "fieldname": "csn_account_reference",
                "fieldtype": "Link",
                "label": "Compte du référentiel officiel",
                "options": "CSN Compte Referentiel",
                "insert_after": "csn_dimensions_section",
            },
            {
                "fieldname": "csn_organisational_unit",
                "fieldtype": "Link",
                "label": "Unité organisationnelle",
                "options": "CSN Unite Organisationnelle",
                "insert_after": "csn_account_reference",
            },
            {
                "fieldname": "csn_source_financement",
                "fieldtype": "Link",
                "label": "Source de financement",
                "options": "CSN Source Financement",
                "insert_after": "csn_organisational_unit",
            },
            {
                "fieldname": "csn_bailleur",
                "fieldtype": "Link",
                "label": "Bailleur",
                "options": "CSN Bailleur",
                "insert_after": "csn_source_financement",
            },
            {
                "fieldname": "csn_convention",
                "fieldtype": "Link",
                "label": "Convention de financement",
                "options": "CSN Convention Financement",
                "insert_after": "csn_bailleur",
            },
            {
                "fieldname": "csn_zone_intervention",
                "fieldtype": "Link",
                "label": "Zone d'intervention",
                "options": "CSN Zone Intervention",
                "insert_after": "csn_convention",
            },
            {
                "fieldname": "csn_budget_line",
                "fieldtype": "Link",
                "label": "Ligne budgétaire PTBA",
                "options": "CSN Ligne PTBA",
                "insert_after": "csn_zone_intervention",
            },
            {
                "fieldname": "csn_fund_reference",
                "fieldtype": "Data",
                "label": "Référence du fonds",
                "insert_after": "csn_budget_line",
            },
            {
                "fieldname": "csn_campaign_reference",
                "fieldtype": "Data",
                "label": "Référence de la campagne",
                "insert_after": "csn_fund_reference",
            },
            {
                "fieldname": "csn_emergency_reference",
                "fieldtype": "Data",
                "label": "Référence de l'urgence",
                "insert_after": "csn_campaign_reference",
            },
            {
                "fieldname": "csn_asset",
                "fieldtype": "Link",
                "label": "Immobilisation",
                "options": "Asset",
                "insert_after": "csn_emergency_reference",
            },
            {
                "fieldname": "csn_inventory_item",
                "fieldtype": "Link",
                "label": "Article de stock",
                "options": "Item",
                "insert_after": "csn_asset",
            },
            {
                "fieldname": "csn_bank_account",
                "fieldtype": "Link",
                "label": "Compte bancaire",
                "options": "Bank Account",
                "insert_after": "csn_inventory_item",
            },
        ],
        "Account": [
            {
                "fieldname": "csn_account_reference",
                "fieldtype": "Link",
                "label": "Compte du référentiel officiel CSN",
                "options": "CSN Compte Referentiel",
                "insert_after": "account_name",
                "unique": 1,
            }
        ],
        "CSN Ligne PTBA": [
            {"fieldname": "csn_execution_section", "fieldtype": "Section Break", "label": "Exécution budgétaire", "insert_after": "budget_amount", "collapsible": 1},
            {"fieldname": "csn_committed_amount", "fieldtype": "Currency", "label": "Crédits engagés", "options": "currency", "read_only": 1, "insert_after": "csn_execution_section"},
            {"fieldname": "csn_liquidated_amount", "fieldtype": "Currency", "label": "Crédits liquidés", "options": "currency", "read_only": 1, "insert_after": "csn_committed_amount"},
            {"fieldname": "csn_paid_amount", "fieldtype": "Currency", "label": "Paiements", "options": "currency", "read_only": 1, "insert_after": "csn_liquidated_amount"},
            {"fieldname": "csn_available_amount", "fieldtype": "Currency", "label": "Crédits disponibles", "options": "currency", "read_only": 1, "insert_after": "csn_paid_amount"},
        ],
        "Purchase Order": [
            {"fieldname": "csn_budget_section", "fieldtype": "Section Break", "label": "Contrôle budgétaire CSN-GHC", "insert_after": "schedule_date", "collapsible": 1},
            {"fieldname": "csn_engagement", "fieldtype": "Link", "label": "Engagement budgétaire", "options": "CSN Engagement Budgetaire", "insert_after": "csn_budget_section", "in_standard_filter": 1},
        ],
        "Purchase Invoice": [
            {"fieldname": "csn_budget_section", "fieldtype": "Section Break", "label": "Liquidation budgétaire CSN-GHC", "insert_after": "bill_date", "collapsible": 1},
            {"fieldname": "csn_engagement", "fieldtype": "Link", "label": "Engagement budgétaire", "options": "CSN Engagement Budgetaire", "insert_after": "csn_budget_section", "in_standard_filter": 1},
        ],
        "Payment Entry": [
            {"fieldname": "csn_budget_section", "fieldtype": "Section Break", "label": "Paiement budgétaire CSN-GHC", "insert_after": "posting_date", "collapsible": 1},
            {"fieldname": "csn_engagement", "fieldtype": "Link", "label": "Engagement budgétaire", "options": "CSN Engagement Budgetaire", "insert_after": "csn_budget_section", "in_standard_filter": 1},
            {"fieldname": "csn_treasury_account", "fieldtype": "Link", "label": "Compte de trésorerie CSN", "options": "CSN Compte Tresorerie", "insert_after": "csn_engagement", "in_standard_filter": 1},
            {"fieldname": "csn_payment_channel", "fieldtype": "Select", "label": "Canal de paiement", "options": "Banque\nEspèces\nMobile Money\nCarte\nPasserelle\nPaiement électronique", "insert_after": "csn_treasury_account"},
            {"fieldname": "csn_exchange_rate_source", "fieldtype": "Data", "label": "Source du taux", "insert_after": "csn_payment_channel"},
            {"fieldname": "csn_exchange_rate_date", "fieldtype": "Date", "label": "Date du taux", "insert_after": "csn_exchange_rate_source"},
            {"fieldname": "csn_exchange_rate_validated_by", "fieldtype": "Link", "label": "Taux validé par", "options": "User", "read_only": 1, "insert_after": "csn_exchange_rate_date"},
        ],
        "Bank Transaction": [
            {"fieldname": "csn_treasury_section", "fieldtype": "Section Break", "label": "Trésorerie CSN-GHC", "insert_after": "bank_account", "collapsible": 1},
            {"fieldname": "csn_treasury_account", "fieldtype": "Link", "label": "Compte de trésorerie CSN", "options": "CSN Compte Tresorerie", "insert_after": "csn_treasury_section", "in_standard_filter": 1},
            {"fieldname": "csn_provider_transaction_id", "fieldtype": "Data", "label": "Identifiant externe", "unique": 1, "insert_after": "csn_treasury_account", "in_standard_filter": 1},
        ],
        "Supplier": [
            {"fieldname": "csn_compliance_section", "fieldtype": "Section Break", "label": "Validation CSN-GHC", "insert_after": "supplier_group", "collapsible": 1},
            {"fieldname": "csn_validation_status", "fieldtype": "Select", "label": "Statut de validation", "options": "Brouillon\nÀ vérifier\nValidé\nSuspendu\nRejeté", "default": "Brouillon", "insert_after": "csn_compliance_section", "in_standard_filter": 1},
            {"fieldname": "csn_legal_documents", "fieldtype": "Attach", "label": "Dossier légal", "insert_after": "csn_validation_status"},
            {"fieldname": "csn_validated_by", "fieldtype": "Link", "label": "Validé par", "options": "User", "read_only": 1, "insert_after": "csn_legal_documents"},
            {"fieldname": "csn_validation_date", "fieldtype": "Datetime", "label": "Date de validation", "read_only": 1, "insert_after": "csn_validated_by"},
        ],
    }
    create_custom_fields(custom_fields, update=True)


def after_install():
    ensure_roles()
    ensure_accounting_custom_fields()
    ensure_master_data()
    ensure_finance_home()


def after_migrate():
    ensure_roles()
    ensure_accounting_custom_fields()
    ensure_master_data()
    ensure_finance_home()
