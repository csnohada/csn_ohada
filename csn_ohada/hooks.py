app_name = "csn_ohada"
app_title = "Finance CSN-GHC"
app_publisher = "CSN-GHC"
app_description = "Gestion financière, budgétaire et comptable SYSCOHADA de la CSN-GHC"
app_email = "daf@finance-csnghc.cloud"
app_license = "gpl-3.0"

# Send non-GET requests for this app's endpoints as native `application/json`
# bodies instead of form-encoded, per-key JSON-stringified values.
use_json_request_body = True

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "csn_ohada",
		"logo": "/assets/csn_ohada/images/csn-ghc-icon.png",
		"title": "Finance CSN-GHC",
		"route": "/app/finance-csn-ghc",
	}
]

# Companion apps that extend a host app (instead of taking their own apps-screen icon) can pin
# their workspaces into the host app's workspace dock (rail) with this hook. Declaring it keeps
# the app off the apps screen, so it takes precedence over any add_to_apps_screen above. Who can
# see a pinned workspace is controlled by that workspace's own Roles table.
# add_to_workspace_dock = [
# 	{
# 		"app": "erpnext",
# 		"workspace": "My Workspace",
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/csn_ohada/css/csn_ohada.css"
# app_include_js = "/assets/csn_ohada/js/csn_ohada.js"

# include js, css files in header of web template
# web_include_css = "/assets/csn_ohada/css/csn_ohada.css"
# web_include_js = "/assets/csn_ohada/js/csn_ohada.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "csn_ohada/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "csn_ohada/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Setup Wizard
# ------------

# open a fresh site's setup in this app's own UI instead of the desk wizard.
# must be a non-desk route (not under /desk or /app); to customize setup within
# desk, use setup_wizard_stages / setup_wizard_complete instead.
# setup_wizard_url = "/csn_ohada/setup"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "csn_ohada.utils.jinja_methods",
# 	"filters": "csn_ohada.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "csn_ohada.install.before_install"
# after_install = "csn_ohada.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "csn_ohada.uninstall.before_uninstall"
# after_uninstall = "csn_ohada.uninstall.after_uninstall"

# Disable / Enable
# ----------------
# Called when this app is logically disabled or re-enabled on a site,
# without uninstalling it. Use this to hide/restore fields this app adds
# to other apps' doctypes.

# before_disable = "csn_ohada.uninstall.before_disable"
# after_disable = "csn_ohada.uninstall.after_disable"
# before_enable = "csn_ohada.install.before_enable"
# after_enable = "csn_ohada.install.after_enable"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "csn_ohada.utils.before_app_install"
# after_app_install = "csn_ohada.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "csn_ohada.utils.before_app_uninstall"
# after_app_uninstall = "csn_ohada.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "csn_ohada.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "csn_ohada.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Journal Entry": {
		"validate": "csn_ohada.accounting_engine.validate_journal_entry",
		"before_submit": "csn_ohada.accounting_engine.before_submit_journal_entry",
		"on_submit": "csn_ohada.accounting_engine.on_submit_journal_entry",
		"before_cancel": "csn_ohada.accounting_engine.prevent_posted_entry_cancellation",
	},
	"Account": {
		"validate": "csn_ohada.accounting_engine.validate_account_mapping",
	},
	"Purchase Order": {
		"validate": "csn_ohada.budget_engine.validate_purchase_order",
	},
	"Purchase Invoice": {
		"validate": "csn_ohada.budget_engine.validate_purchase_invoice",
		"on_submit": "csn_ohada.budget_engine.post_purchase_invoice",
		"on_cancel": "csn_ohada.budget_engine.cancel_purchase_invoice",
	},
	"Payment Entry": {
		"validate": [
			"csn_ohada.budget_engine.validate_payment_entry",
			"csn_ohada.treasury_engine.validate_payment_treasury",
		],
		"on_submit": "csn_ohada.budget_engine.post_payment_entry",
		"on_cancel": "csn_ohada.budget_engine.cancel_payment_entry",
	},
	"Supplier": {
		"validate": "csn_ohada.budget_engine.validate_supplier",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"csn_ohada.tasks.all"
# 	],
# 	"daily": [
# 		"csn_ohada.tasks.daily"
# 	],
# 	"hourly": [
# 		"csn_ohada.tasks.hourly"
# 	],
# 	"weekly": [
# 		"csn_ohada.tasks.weekly"
# 	],
# 	"monthly": [
# 		"csn_ohada.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "csn_ohada.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "csn_ohada.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "csn_ohada.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "csn_ohada.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["csn_ohada.utils.before_request"]
# after_request = ["csn_ohada.utils.after_request"]

# Job Events
# ----------
# before_job = ["csn_ohada.utils.before_job"]
# after_job = ["csn_ohada.utils.after_job"]

# after_file_upload = ["csn_ohada.utils.after_file_upload"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"csn_ohada.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# Require all whitelisted methods to have type annotations
require_type_annotated_api_methods = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


after_install = "csn_ohada.install.after_install"
after_migrate = "csn_ohada.install.after_migrate"
