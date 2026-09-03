frappe.query_reports["CSN Grand Livre"] = {
	filters: [
		{ fieldname: "company", label: __("Entité juridique"), fieldtype: "Link", options: "Company", reqd: 1, default: frappe.defaults.get_user_default("Company") },
		{ fieldname: "from_date", label: __("Du"), fieldtype: "Date", reqd: 1, default: frappe.datetime.year_start() },
		{ fieldname: "to_date", label: __("Au"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
		{ fieldname: "account", label: __("Compte"), fieldtype: "Link", options: "Account" },
		{ fieldname: "party_type", label: __("Type de tiers"), fieldtype: "Link", options: "DocType" },
		{ fieldname: "party", label: __("Tiers"), fieldtype: "Dynamic Link", options: "party_type" },
	],
};
