from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_validate(filters)
	conditions = ["gle.company=%(company)s", "gle.is_cancelled=0", "gle.posting_date between %(from_date)s and %(to_date)s"]
	values = {"company": filters.company, "from_date": filters.from_date, "to_date": filters.to_date}
	if filters.account:
		conditions.append("gle.account=%(account)s")
		values["account"] = filters.account
	rows = frappe.db.sql(
		f"""select acc.account_number, gle.account, acc.account_name,
		sum(gle.debit) debit, sum(gle.credit) credit, sum(gle.debit-gle.credit) balance
		from `tabGL Entry` gle inner join `tabAccount` acc on acc.name=gle.account
		where {' and '.join(conditions)} group by acc.account_number, gle.account, acc.account_name
		order by coalesce(acc.account_number,''), gle.account""", values, as_dict=True,
	)
	if not filters.show_zero_balance:
		rows = [row for row in rows if Decimal(str(row.balance or 0)) != 0]
	return _columns(), rows


def _validate(filters):
	if not filters.company or not filters.from_date or not filters.to_date:
		frappe.throw(_("L'entité et les dates sont obligatoires."))
	if getdate(filters.to_date) < getdate(filters.from_date):
		frappe.throw(_("Plage de dates invalide."))
	company = frappe.get_doc("Company", filters.company)
	if not frappe.has_permission("Company", "read", doc=company):
		frappe.throw(_("Accès refusé."), frappe.PermissionError)


def _columns():
	return [
		{"fieldname": "account_number", "label": _("Numéro"), "fieldtype": "Data", "width": 100},
		{"fieldname": "account", "label": _("Compte"), "fieldtype": "Link", "options": "Account", "width": 280},
		{"fieldname": "account_name", "label": _("Libellé"), "fieldtype": "Data", "width": 220},
		{"fieldname": "debit", "label": _("Débit"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "credit", "label": _("Crédit"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "balance", "label": _("Solde"), "fieldtype": "Currency", "width": 160},
	]
