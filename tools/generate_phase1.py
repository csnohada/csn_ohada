"""Generate Phase 1 Frappe DocTypes for the CSN-GHC accounting foundation."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = ROOT / "csn_ohada" / "csn_ohada" / "doctype"


ADMIN = {
    "role": "System Manager",
    "read": 1,
    "write": 1,
    "create": 1,
    "delete": 1,
    "submit": 1,
    "cancel": 1,
    "amend": 1,
    "report": 1,
    "export": 1,
    "print": 1,
    "email": 1,
    "share": 1,
}


def permission(role: str, *, write: bool = False, submit: bool = False) -> dict:
    result = {"role": role, "read": 1, "report": 1, "export": 1, "print": 1}
    if write:
        result.update({"write": 1, "create": 1})
    if submit:
        result.update({"submit": 1, "cancel": 1, "amend": 1})
    return result


def field(fieldname: str, fieldtype: str, label: str, **kwargs) -> dict:
    return {"fieldname": fieldname, "fieldtype": fieldtype, "label": label, **kwargs}


def write_doctype(
    name: str,
    fields: list[dict],
    *,
    permissions: list[dict],
    autoname: str = "field:code",
    title_field: str | None = None,
    search_fields: str = "code",
    is_submittable: bool = False,
    issingle: bool = False,
    controller: str,
) -> None:
    scrub = name.lower().replace(" ", "_")
    folder = DOCTYPE_ROOT / scrub
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "__init__.py").touch()

    definition = {
        "actions": [],
        "allow_rename": 0,
        "doctype": "DocType",
        "engine": "InnoDB",
        "field_order": [item["fieldname"] for item in fields],
        "fields": fields,
        "index_web_pages_for_search": 0,
        "links": [],
        "module": "CSN OHADA",
        "name": name,
        "permissions": permissions,
        "sort_field": "modified",
        "sort_order": "DESC",
        "states": [],
        "track_changes": 1,
    }
    if issingle:
        definition["issingle"] = 1
    else:
        definition.update(
            {
                "autoname": autoname,
                "naming_rule": "By fieldname" if autoname.startswith("field:") else "By Naming Series",
                "search_fields": search_fields,
            }
        )
    if title_field:
        definition["title_field"] = title_field
    if is_submittable:
        definition["is_submittable"] = 1

    (folder / f"{scrub}.json").write_text(
        json.dumps(definition, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (folder / f"{scrub}.py").write_text(controller.strip() + "\n", encoding="utf-8")


write_doctype(
    "CSN Unite Organisationnelle",
    [
        field("code", "Data", "Code", reqd=1, unique=1, in_list_view=1),
        field("unit_name", "Data", "Unité organisationnelle", reqd=1, in_list_view=1),
        field(
            "unit_type",
            "Select",
            "Type d'unité",
            options="Institution\nDirection\nDivision\nBureau\nAntenne provinciale\nProjet\nProgramme\nEntrepôt\nUnité de gestion\nSite opérationnel",
            reqd=1,
            in_list_view=1,
        ),
        field("parent_unit", "Link", "Unité parente", options="CSN Unite Organisationnelle"),
        field("company", "Link", "Entité juridique", options="Company", reqd=1),
        field("cost_center", "Link", "Centre de coûts", options="Cost Center"),
        field("province", "Data", "Province", in_list_view=1),
        field("manager", "Link", "Responsable", options="User"),
        field("is_budget_center", "Check", "Centre budgétaire", default="0"),
        field("is_responsibility_center", "Check", "Centre de responsabilité", default="1"),
        field("is_reporting_unit", "Check", "Unité de reporting", default="1"),
        field("disabled", "Check", "Désactivée", default="0", in_list_view=1),
    ],
    permissions=[
        ADMIN,
        permission("CSN Administrateur Technique", write=True),
        permission("CSN Directeur Financier", write=True),
        permission("CSN Auditeur Interne"),
        permission("CSN Responsable Antenne"),
    ],
    title_field="unit_name",
    search_fields="code,unit_name,unit_type,province",
    controller='''
import frappe
from frappe import _
from frappe.model.document import Document


class CSNUniteOrganisationnelle(Document):
    def validate(self):
        if self.parent_unit == self.name:
            frappe.throw(_("Une unité ne peut pas être son propre parent."))

        if self.parent_unit:
            parent_company = frappe.db.get_value(
                "CSN Unite Organisationnelle", self.parent_unit, "company"
            )
            if parent_company and parent_company != self.company:
                frappe.throw(_("L'unité parente doit appartenir à la même entité juridique."))

        if self.cost_center:
            cost_center_company = frappe.db.get_value("Cost Center", self.cost_center, "company")
            if cost_center_company != self.company:
                frappe.throw(_("Le centre de coûts doit appartenir à l'entité juridique sélectionnée."))
''',
)

write_doctype(
    "CSN Referentiel Comptable",
    [
        field(
            "code",
            "Select",
            "Code du référentiel",
            options="SYSCOHADA_REVISED\nPCE_RDC\nOTHER_OFFICIAL_FRAMEWORK",
            reqd=1,
            unique=1,
            in_list_view=1,
        ),
        field("framework_name", "Data", "Intitulé officiel", reqd=1, in_list_view=1),
        field("jurisdiction", "Data", "Juridiction", default="RDC"),
        field("legal_reference", "Small Text", "Référence juridique ou administrative", reqd=1),
        field("source_document", "Attach", "Document source officiel", reqd=1),
        field("description", "Text Editor", "Description"),
        field("disabled", "Check", "Désactivé", default="0", in_list_view=1),
    ],
    permissions=[
        ADMIN,
        permission("CSN Administrateur Referentiel", write=True),
        permission("CSN Directeur Financier"),
        permission("CSN Auditeur Interne"),
    ],
    title_field="framework_name",
    search_fields="code,framework_name,jurisdiction",
    controller='''
from frappe.model.document import Document


class CSNReferentielComptable(Document):
    pass
''',
)

write_doctype(
    "CSN Version Referentiel Comptable",
    [
        field("code", "Data", "Code de version", reqd=1, unique=1, in_list_view=1),
        field("framework", "Link", "Référentiel", options="CSN Referentiel Comptable", reqd=1, in_list_view=1),
        field("version_label", "Data", "Version officielle", reqd=1),
        field("valid_from", "Date", "Valide à partir du", reqd=1, in_list_view=1),
        field("valid_to", "Date", "Valide jusqu'au"),
        field(
            "status",
            "Select",
            "Statut",
            options="Brouillon\nImportée\nValidée\nApprouvée\nActive\nInactive",
            default="Brouillon",
            reqd=1,
            in_list_view=1,
        ),
        field("legal_reference", "Small Text", "Référence juridique ou administrative", reqd=1),
        field("source_document", "Attach", "Plan officiel importé", reqd=1),
        field("source_checksum", "Data", "Empreinte SHA-256 du fichier", read_only=1),
        field("framework_admin_validator", "Link", "Validateur du référentiel", options="User"),
        field("finance_validator", "Link", "Responsable financier validateur", options="User"),
        field("approving_authority", "Link", "Autorité approbatrice", options="User"),
        field("approval_date", "Date", "Date d'approbation"),
        field("notes", "Small Text", "Observations"),
    ],
    permissions=[
        ADMIN,
        permission("CSN Administrateur Referentiel", write=True),
        permission("CSN Directeur Financier", write=True),
        permission("CSN Direction Generale", write=True),
        permission("CSN Auditeur Interne"),
    ],
    title_field="version_label",
    search_fields="code,framework,version_label,status",
    controller='''
import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class CSNVersionReferentielComptable(Document):
    def validate(self):
        if self.valid_to and getdate(self.valid_to) < getdate(self.valid_from):
            frappe.throw(_("La fin de validité ne peut pas précéder la prise d'effet."))

        if self.status in ("Approuvée", "Active"):
            required = (
                "framework_admin_validator",
                "finance_validator",
                "approving_authority",
                "approval_date",
                "legal_reference",
                "source_document",
            )
            missing = [self.meta.get_label(item) for item in required if not self.get(item)]
            if missing:
                frappe.throw(_("Activation impossible. Champs manquants : {0}").format(", ".join(missing)))

        if self.status == "Active":
            other = frappe.db.exists(
                "CSN Version Referentiel Comptable",
                {"framework": self.framework, "status": "Active", "name": ["!=", self.name or ""]},
            )
            if other:
                frappe.throw(_("Une seule version active est autorisée par référentiel."))

    def before_save(self):
        if self.source_document:
            file_url = frappe.db.get_value("File", {"file_url": self.source_document}, "name")
            if file_url:
                file_doc = frappe.get_doc("File", file_url)
                content = file_doc.get_content()
                if isinstance(content, str):
                    content = content.encode()
                self.source_checksum = hashlib.sha256(content).hexdigest()
''',
)

write_doctype(
    "CSN Compte Referentiel",
    [
        field("code", "Data", "Identifiant interne", reqd=1, unique=1, hidden=1),
        field("framework_version", "Link", "Version du référentiel", options="CSN Version Referentiel Comptable", reqd=1, in_list_view=1),
        field("account_code", "Data", "Code du compte", reqd=1, in_list_view=1),
        field("account_label", "Data", "Libellé du compte", reqd=1, in_list_view=1),
        field("parent_account_code", "Data", "Code du compte parent"),
        field("account_class", "Data", "Classe"),
        field("account_category", "Data", "Catégorie"),
        field("normal_balance", "Select", "Sens normal", options="Débit\nCrédit", reqd=1),
        field("is_postable", "Check", "Imputable", default="1"),
        field("is_control_account", "Check", "Compte collectif", default="0"),
        field("requires_third_party", "Check", "Tiers obligatoire", default="0"),
        field("requires_budget_line", "Check", "Ligne budgétaire obligatoire", default="0"),
        field("requires_project", "Check", "Projet obligatoire", default="0"),
        field("requires_fund", "Check", "Fonds obligatoire", default="0"),
        field("requires_donor", "Check", "Bailleur ou donateur obligatoire", default="0"),
        field("requires_campaign", "Check", "Campagne obligatoire", default="0"),
        field("requires_emergency", "Check", "Urgence obligatoire", default="0"),
        field("requires_cost_center", "Check", "Centre de coûts obligatoire", default="0"),
        field("requires_asset", "Check", "Immobilisation obligatoire", default="0"),
        field("requires_inventory_item", "Check", "Article de stock obligatoire", default="0"),
        field("requires_bank_account", "Check", "Compte bancaire obligatoire", default="0"),
        field("valid_from", "Date", "Valide à partir du", reqd=1),
        field("valid_to", "Date", "Valide jusqu'au"),
        field("legal_reference", "Small Text", "Référence juridique"),
        field("source_document", "Data", "Référence du document source"),
        field("status", "Select", "Statut", options="Brouillon\nActif\nDésactivé\nFermé", default="Brouillon", reqd=1, in_list_view=1),
    ],
    permissions=[
        ADMIN,
        permission("CSN Administrateur Referentiel", write=True),
        permission("CSN Directeur Financier"),
        permission("CSN Comptable"),
        permission("CSN Auditeur Interne"),
    ],
    title_field="account_label",
    search_fields="account_code,account_label,parent_account_code,framework_version",
    controller='''
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class CSNCompteReferentiel(Document):
    def autoname(self):
        self.code = f"{self.framework_version}::{self.account_code}"
        self.name = self.code

    def validate(self):
        if self.valid_to and getdate(self.valid_to) < getdate(self.valid_from):
            frappe.throw(_("La fin de validité ne peut pas précéder la date de début."))
        if self.parent_account_code == self.account_code:
            frappe.throw(_("Un compte ne peut pas être son propre parent."))

        version_status = frappe.db.get_value(
            "CSN Version Referentiel Comptable", self.framework_version, "status"
        )
        if version_status in ("Active", "Inactive") and self.has_value_changed("account_code"):
            frappe.throw(_("Les codes d'une version active ou historique sont immuables."))

        if self.parent_account_code:
            parent = frappe.db.exists(
                "CSN Compte Referentiel",
                {
                    "framework_version": self.framework_version,
                    "account_code": self.parent_account_code,
                },
            )
            if not parent:
                frappe.throw(_("Le compte parent n'existe pas dans cette version du référentiel."))

    def on_trash(self):
        if self.status in ("Actif", "Fermé"):
            frappe.throw(_("Un compte activé ou historique ne peut pas être supprimé."))
''',
)

write_doctype(
    "CSN Periode Comptable",
    [
        field("naming_series", "Select", "Série", options="PER-.YYYY.-.###", default="PER-.YYYY.-.###", reqd=1),
        field("period_name", "Data", "Période", reqd=1, in_list_view=1),
        field("company", "Link", "Entité juridique", options="Company", reqd=1, in_list_view=1),
        field("fiscal_year", "Link", "Exercice fiscal", options="Fiscal Year", reqd=1, in_list_view=1),
        field("start_date", "Date", "Date de début", reqd=1),
        field("end_date", "Date", "Date de fin", reqd=1),
        field("status", "Select", "Statut", options="Ouverte\nEn clôture\nClôturée\nRéouverte", default="Ouverte", reqd=1, in_list_view=1),
        field("closed_by", "Link", "Clôturée par", options="User", read_only=1),
        field("closed_on", "Datetime", "Clôturée le", read_only=1),
        field("reopening_reason", "Small Text", "Justification de réouverture"),
        field("reopened_by", "Link", "Réouverte par", options="User", read_only=1),
        field("reopened_on", "Datetime", "Réouverte le", read_only=1),
    ],
    permissions=[
        ADMIN,
        permission("CSN Chef Comptabilite", write=True),
        permission("CSN Directeur Financier", write=True),
        permission("CSN Comptable"),
        permission("CSN Auditeur Interne"),
    ],
    autoname="naming_series:",
    title_field="period_name",
    search_fields="period_name,company,fiscal_year,status",
    controller='''
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
''',
)

write_doctype(
    "CSN Parametres Comptables",
    [
        field("company", "Link", "Entité juridique CSN-GHC", options="Company", reqd=1),
        field(
            "accounting_primary_framework",
            "Link",
            "ACCOUNTING_PRIMARY_FRAMEWORK",
            options="CSN Referentiel Comptable",
        ),
        field(
            "primary_framework_version",
            "Link",
            "Version principale active",
            options="CSN Version Referentiel Comptable",
        ),
        field(
            "secondary_reporting_framework",
            "Link",
            "SECONDARY_REPORTING_FRAMEWORK",
            options="CSN Referentiel Comptable",
        ),
        field("enable_dual_reporting", "Check", "Activer CSNGHC_DUAL_REPORTING", default="0"),
        field("effective_date", "Date", "Date de prise d'effet"),
    ],
    permissions=[
        ADMIN,
        permission("CSN Administrateur Referentiel", write=True),
        permission("CSN Directeur Financier"),
        permission("CSN Auditeur Interne"),
    ],
    issingle=True,
    controller='''
import frappe
from frappe import _
from frappe.model.document import Document


class CSNParametresComptables(Document):
    def validate(self):
        if self.enable_dual_reporting and not self.secondary_reporting_framework:
            frappe.throw(_("Le référentiel secondaire est obligatoire en mode dual reporting."))
        if self.secondary_reporting_framework == self.accounting_primary_framework:
            frappe.throw(_("Les référentiels principal et secondaire doivent être différents."))

        if self.primary_framework_version:
            version = frappe.db.get_value(
                "CSN Version Referentiel Comptable",
                self.primary_framework_version,
                ["framework", "status", "framework_admin_validator", "finance_validator", "approving_authority", "legal_reference", "source_document"],
                as_dict=True,
            )
            if not version or version.framework != self.accounting_primary_framework:
                frappe.throw(_("La version sélectionnée n'appartient pas au référentiel principal."))
            if version.status != "Active":
                frappe.throw(_("La version principale doit être active."))
            required = ("framework_admin_validator", "finance_validator", "approving_authority", "legal_reference", "source_document")
            if any(not version.get(item) for item in required):
                frappe.throw(_("Le référentiel principal ne satisfait pas le circuit de validation requis."))
''',
)

print("Phase 1 DocTypes generated.")
