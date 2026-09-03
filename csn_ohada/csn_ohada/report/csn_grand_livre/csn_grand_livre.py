import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.company or not filters.from_date or not filters.to_date:
		frappe.throw(_("L'entité et les dates sont obligatoires."))
	if getdate(filters.to_date) < getdate(filters.from_date):
		frappe.throw(_("Plage de dates invalide."))
	company = frappe.get_doc("Company", filters.company)
	if not frappe.has_permission("Company", "read", doc=company):
		frappe.throw(_("Accès refusé."), frappe.PermissionError)
	conditions = ["gle.company=%(company)s", "gle.is_cancelled=0", "gle.posting_date between %(from_date)s and %(to_date)s"]
	values = {"company": filters.company, "from_date": filters.from_date, "to_date": filters.to_date}
	for key in ("account", "party_type", "party"):
		if filters.get(key):
			conditions.append(f"gle.{key}=%({key})s")
			values[key] = filters.get(key)
	rows = frappe.db.sql(
		f"""select gle.posting_date, acc.account_number, gle.account, gle.voucher_type,
		gle.voucher_no, gle.party_type, gle.party, gle.debit, gle.credit, gle.cost_center,
		gle.project, gle.remarks from `tabGL Entry` gle inner join `tabAccount` acc on acc.name=gle.account
		where {' and '.join(conditions)} order by coalesce(acc.account_number,''), gle.account, gle.posting_date, gle.creation""",
		values, as_dict=True,
	)
	running = {}
	for row in rows:
		running[row.account] = running.get(row.account, 0) + (row.debit or 0) - (row.credit or 0)
		row.balance = running[row.account]
	return _columns(), rows


def _columns():
	return [
		{"fieldname": "posting_date", "label": _("Date"), "fieldtype": "Date", "width": 105},
		{"fieldname": "account_number", "label": _("Numéro"), "fieldtype": "Data", "width": 95},
		{"fieldname": "account", "label": _("Compte"), "fieldtype": "Link", "options": "Account", "width": 240},
		{"fieldname": "voucher_type", "label": _("Type"), "fieldtype": "Data", "width": 120},
		{"fieldname": "voucher_no", "label": _("Pièce"), "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
		{"fieldname": "party", "label": _("Tiers"), "fieldtype": "Dynamic Link", "options": "party_type", "width": 160},
		{"fieldname": "debit", "label": _("Débit"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "credit", "label": _("Crédit"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "balance", "label": _("Solde cumulé"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "cost_center", "label": _("Centre de coûts"), "fieldtype": "Link", "options": "Cost Center", "width": 170},
		{"fieldname": "project", "label": _("Projet"), "fieldtype": "Link", "options": "Project", "width": 150},
		{"fieldname": "remarks", "label": _("Libellé"), "fieldtype": "Data", "width": 240},
	]
