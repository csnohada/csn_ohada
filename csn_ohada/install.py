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


def ensure_roles():
    """Crée de manière idempotente les rôles du manuel CSN-GHC."""
    for role_name in CSN_ROLES:
        if frappe.db.exists("Role", role_name):
            continue

        role = frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
                "is_custom": 0,
                "disabled": 0,
            }
        )
        role.insert(ignore_permissions=True)

    frappe.db.commit()


def after_install():
    ensure_roles()


def after_migrate():
    ensure_roles()
