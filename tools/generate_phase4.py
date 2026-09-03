"""Generate Phase 4 treasury and reconciliation DocTypes."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "csn_ohada" / "csn_ohada" / "doctype"


def field(name, kind, label, **kwargs):
	return {"fieldname": name, "fieldtype": kind, "label": label, **kwargs}


def permissions():
	return [
		{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1, "print": 1},
		{"role": "CSN Trésorier", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1, "print": 1},
		{"role": "CSN Directeur Financier", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1, "print": 1},
		{"role": "CSN Comptable", "read": 1, "report": 1, "export": 1, "print": 1},
		{"role": "CSN Auditeur Interne", "read": 1, "report": 1, "export": 1, "print": 1},
	]


def write(name, fields, controller, *, autoname="naming_series:", submittable=False, title=None, search=""):
	scrub = name.lower().replace(" ", "_")
	folder = BASE / scrub
	folder.mkdir(parents=True, exist_ok=True)
	(folder / "__init__.py").touch()
	payload = {
		"actions": [], "allow_rename": 0, "autoname": autoname, "doctype": "DocType", "engine": "InnoDB",
		"field_order": [row["fieldname"] for row in fields], "fields": fields, "index_web_pages_for_search": 0,
		"links": [], "module": "CSN OHADA", "name": name,
		"naming_rule": "By fieldname" if autoname.startswith("field:") else "By Naming Series",
		"permissions": permissions(), "search_fields": search, "sort_field": "modified", "sort_order": "DESC",
		"states": [], "track_changes": 1,
	}
	if submittable:
		payload["is_submittable"] = 1
	if title:
		payload["title_field"] = title
	(folder / f"{scrub}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
	(folder / f"{scrub}.py").write_text(controller.strip() + "\n", encoding="utf-8")


write(
	"CSN Compte Tresorerie",
	[
		field("code", "Data", "Code", reqd=1, unique=1, in_list_view=1),
		field("treasury_name", "Data", "Compte de trésorerie", reqd=1, in_list_view=1),
		field("company", "Link", "Entité juridique", options="Company", reqd=1),
		field("treasury_type", "Select", "Type", options="Banque\nCaisse\nMobile Money\nPaiement électronique\nCollecte\nProjet\nBailleur\nCampagne\nTransit", reqd=1, in_list_view=1),
		field("account", "Link", "Compte comptable", options="Account", reqd=1, in_list_view=1),
		field("bank_account", "Link", "Compte bancaire ERPNext", options="Bank Account"),
		field("currency", "Link", "Devise", options="Currency", reqd=1, in_list_view=1),
		field("provider", "Data", "Banque ou opérateur"),
		field("account_identifier", "Data", "Numéro ou identifiant du compte"),
		field("organisational_unit", "Link", "Unité responsable", options="CSN Unite Organisationnelle"),
		field("responsible_user", "Link", "Responsable", options="User"),
		field("reconciliation_tolerance", "Currency", "Tolérance de rapprochement", options="currency", default="0"),
		field("disabled", "Check", "Désactivé", default="0", in_list_view=1),
	],
	'''from frappe.model.document import Document


class CSNCompteTresorerie(Document):
	def validate(self):
		from csn_ohada.treasury_engine import validate_treasury_account
		validate_treasury_account(self)
''',
	autoname="field:code", title="treasury_name", search="code,treasury_name,treasury_type,account_identifier",
)

write(
	"CSN Operation Tresorerie",
	[
		field("naming_series", "Select", "Série", options="OT-.YYYY.-.######", default="OT-.YYYY.-.######", reqd=1),
		field("treasury_account", "Link", "Compte de trésorerie", options="CSN Compte Tresorerie", reqd=1, in_list_view=1),
		field("company", "Link", "Entité juridique", options="Company", reqd=1),
		field("transaction_date", "Date", "Date de transaction", reqd=1, in_list_view=1),
		field("settlement_date", "Date", "Date de règlement"),
		field("operation_type", "Select", "Type", options="Encaissement\nDécaissement\nVirement interne\nDépôt\nRetrait\nFrais\nRemboursement", reqd=1, in_list_view=1),
		field("channel", "Select", "Canal", options="Banque\nEspèces\nMobile Money\nCarte\nPasserelle\nPaiement électronique", reqd=1),
		field("provider_transaction_id", "Data", "Identifiant fournisseur", unique=1, in_list_view=1),
		field("gross_amount", "Currency", "Montant brut", options="original_currency", reqd=1),
		field("fee_amount", "Currency", "Frais", options="original_currency", default="0"),
		field("net_amount", "Currency", "Montant net", options="original_currency", read_only=1, in_list_view=1),
		field("original_currency", "Link", "Devise d'origine", options="Currency", reqd=1),
		field("settlement_currency", "Link", "Devise de règlement", options="Currency", reqd=1),
		field("exchange_rate", "Float", "Taux de change", default="1", reqd=1),
		field("amount_cdf", "Currency", "Montant en CDF", read_only=1),
		field("exchange_rate_source", "Data", "Source du taux"),
		field("exchange_rate_date", "Date", "Date du taux"),
		field("payment_entry", "Link", "Écriture de paiement", options="Payment Entry"),
		field("bank_transaction", "Link", "Transaction bancaire", options="Bank Transaction"),
		field("supporting_document", "Attach", "Pièce justificative"),
		field("status", "Select", "Statut", options="Importée\nConfirmée\nRapprochée\nComptabilisée\nAnnulée", default="Importée", read_only=1, in_list_view=1),
		field("amended_from", "Link", "Rectification de", options="CSN Operation Tresorerie", read_only=1, no_copy=1),
	],
	'''from frappe.model.document import Document


class CSNOperationTresorerie(Document):
	def validate(self):
		from csn_ohada.treasury_engine import validate_treasury_operation
		validate_treasury_operation(self)

	def before_submit(self):
		self.status = "Confirmée"

	def on_cancel(self):
		from csn_ohada.treasury_engine import cancel_treasury_operation
		cancel_treasury_operation(self)
''',
	submittable=True, title="provider_transaction_id", search="provider_transaction_id,treasury_account,status,payment_entry",
)

write(
	"CSN Rapprochement Tresorerie",
	[
		field("naming_series", "Select", "Série", options="RAP-.YYYY.-.######", default="RAP-.YYYY.-.######", reqd=1),
		field("reconciliation_date", "Date", "Date de rapprochement", reqd=1, in_list_view=1),
		field("treasury_operation", "Link", "Opération de trésorerie", options="CSN Operation Tresorerie", reqd=1, in_list_view=1),
		field("payment_entry", "Link", "Écriture de paiement", options="Payment Entry", reqd=1, in_list_view=1),
		field("statement_amount", "Currency", "Montant du relevé", options="currency", read_only=1),
		field("accounting_amount", "Currency", "Montant comptable", options="currency", read_only=1),
		field("difference_amount", "Currency", "Écart", options="currency", read_only=1, in_list_view=1),
		field("currency", "Link", "Devise", options="Currency", read_only=1),
		field("justification", "Small Text", "Justification de l'écart"),
		field("initiated_by", "Link", "Initié par", options="User", read_only=1),
		field("approved_by", "Link", "Approuvé par", options="User", read_only=1),
		field("status", "Select", "Statut", options="Brouillon\nRapproché\nAnnulé", default="Brouillon", read_only=1, in_list_view=1),
		field("amended_from", "Link", "Rectification de", options="CSN Rapprochement Tresorerie", read_only=1, no_copy=1),
	],
	'''from frappe.model.document import Document


class CSNRapprochementTresorerie(Document):
	def validate(self):
		from csn_ohada.treasury_engine import validate_reconciliation
		validate_reconciliation(self)

	def before_submit(self):
		from csn_ohada.treasury_engine import approve_reconciliation
		approve_reconciliation(self)

	def on_submit(self):
		from csn_ohada.treasury_engine import post_reconciliation
		post_reconciliation(self)

	def on_cancel(self):
		from csn_ohada.treasury_engine import cancel_reconciliation
		cancel_reconciliation(self)
''',
	submittable=True, title="treasury_operation", search="treasury_operation,payment_entry,status",
)

print("Phase 4 DocTypes generated.")
