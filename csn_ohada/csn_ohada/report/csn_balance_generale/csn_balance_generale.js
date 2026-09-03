frappe.query_reports["CSN Balance Generale"] = {
	filters: [
		{ fieldname: "company", label: __("Entité juridique"), fieldtype: "Link", options: "Company", reqd: 1, default: frappe.defaults.get_user_default("Company") },
		{ fieldname: "from_date", label: __("Du"), fieldtype: "Date", reqd: 1, default: frappe.datetime.year_start() },
		{ fieldname: "to_date", label: __("Au"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
		{ fieldname: "account", label: __("Compte"), fieldtype: "Link", options: "Account" },
		{ fieldname: "show_zero_balance", label: __("Afficher les soldes nuls"), fieldtype: "Check", default: 0 },
	],
};
