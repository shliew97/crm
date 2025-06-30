import frappe
from frappe import _

from crm.api.doc import get_fields_meta, get_assigned_users
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script
from collections import defaultdict
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.whatsapp_message import create_crm_tagging_assignment, create_crm_lead_assignment
from frappe.utils.user import get_users_with_role

@frappe.whitelist()
def get_lead(name):
	Lead = frappe.qb.DocType("CRM Lead")

	query = frappe.qb.from_(Lead).select("*").where(Lead.name == name).limit(1)

	lead = query.run(as_dict=True)
	if not len(lead):
		frappe.throw(_("Lead not found"), frappe.DoesNotExistError)
	lead = lead.pop()

	lead["doctype"] = "CRM Lead"
	lead["fields_meta"] = get_fields_meta("CRM Lead")
	lead["_form_script"] = get_form_script('CRM Lead')
	lead["_assign"] = get_assigned_users("CRM Lead", lead.name, lead.owner)
	lead["_assignments"] = frappe.db.get_list("CRM Lead Assignment", filters={"crm_lead": name}, pluck="status")
	return lead

@frappe.whitelist()
def get_new_leads(search_text=None, off_work_mode=False):
	user_roles = frappe.get_roles()

	if search_text:
		search_text_condition = """AND cl.mobile_no LIKE "%%{0}%%" """.format(search_text)

		leads = frappe.db.sql("""
			SELECT
				cl.*, cla.status AS cla_status, clt.tagging
			FROM `tabCRM Lead` cl
			LEFT JOIN `tabCRM Lead Assignment` cla
			ON cl.name = cla.crm_lead
			LEFT JOIN `tabCRM Lead Tagging` clt
			ON cl.name = clt.crm_lead AND clt.status = "Open"
			WHERE 1=1
		"""
		+
		search_text_condition
		+
		"""
			ORDER BY
			CASE
				WHEN cla.status = 'Accepted' THEN 1
				WHEN cl.alert = 1 THEN 2
				WHEN cla.status = 'New' THEN 3
				WHEN cla.status = 'Completed' THEN 4
				WHEN cla.status = 'Case Closed' THEN 5
				ELSE 6
			END,
			cl.conversation_start_at
		""", as_dict=1)
	elif "Booking Centre" in user_roles and "System Manager" not in user_roles:
		values = {
			"user": frappe.session.user,
		}

		off_work_mode_query = ""

		if off_work_mode:
			off_work_mode_query = "AND cl.conversation_start_at < CURDATE() + INTERVAL 21 HOUR AND cl.last_reply_at < CURDATE() + INTERVAL 21 HOUR"

		leads = frappe.db.sql("""
			SELECT
				cl.*, cla.status AS cla_status, clt.tagging
			FROM `tabCRM Lead` cl
			JOIN `tabCRM Lead Assignment` cla
			ON cl.name = cla.crm_lead
			JOIN `tabUser Permission` up
			ON cla.whatsapp_message_templates = up.for_value AND up.allow = "WhatsApp Message Templates" AND up.user = %(user)s
			LEFT JOIN `tabCRM Lead Tagging` clt
			ON cl.name = clt.crm_lead AND clt.status = "Open"
			WHERE cla.status IN ("New", "Accepted")
			AND (cla.accepted_by IS NULL OR cla.accepted_by = %(user)s)
		"""
		+ off_work_mode_query +
		"""
			ORDER BY
			CASE
				WHEN cla.status = 'Accepted' THEN 1
				WHEN cl.alert = 1 THEN 2
				WHEN cla.status = 'New' THEN 3
				WHEN cla.status = 'Completed' THEN 4
				WHEN cla.status = 'Case Closed' THEN 5
				ELSE 6
			END,
			cl.conversation_start_at
		""", values=values, as_dict=1)
	elif "CRM Agent" in user_roles and "System Manager" not in user_roles:
		values = {
			"user": frappe.session.user,
		}

		leads = frappe.db.sql("""
			SELECT
				cl.*, cla.status AS cla_status, clt.tagging
			FROM `tabCRM Lead` cl
			JOIN `tabCRM Lead Assignment` cla
			ON cl.name = cla.crm_lead
			JOIN `tabUser Permission` up
			ON cla.whatsapp_message_templates = up.for_value AND up.allow = "WhatsApp Message Templates" AND up.user = %(user)s
			LEFT JOIN `tabCRM Lead Tagging` clt
			ON cl.name = clt.crm_lead AND clt.status = "Open"
			WHERE cla.status IN ("New", "Accepted")
			ORDER BY
			CASE
				WHEN cla.status = 'Accepted' THEN 1
				WHEN cl.alert = 1 THEN 2
				WHEN cla.status = 'New' THEN 3
				WHEN cla.status = 'Completed' THEN 4
				WHEN cla.status = 'Case Closed' THEN 5
				ELSE 6
			END,
			cl.conversation_start_at
		""", values=values, as_dict=1)
	else:
		values = {
			"user": frappe.session.user,
		}

		leads = frappe.db.sql("""
			SELECT
				cl.*, cla.status AS cla_status, clt.tagging
			FROM `tabCRM Lead` cl
			JOIN `tabCRM Lead Assignment` cla
			ON cl.name = cla.crm_lead
			LEFT JOIN `tabCRM Lead Tagging` clt
			ON cl.name = clt.crm_lead AND clt.status = "Open"
			WHERE cla.status IN ("New", "Accepted")
			ORDER BY
			CASE
				WHEN cla.status = 'Accepted' THEN 1
				WHEN cl.alert = 1 THEN 2
				WHEN cla.status = 'New' THEN 3
				WHEN cla.status = 'Completed' THEN 4
				WHEN cla.status = 'Case Closed' THEN 5
				ELSE 6
			END,
			cl.conversation_start_at
		""", values=values, as_dict=1)

	if not leads:
		leads = []

	leads_defaultdict = defaultdict(lambda: {
		"name": "",
		"lead_name": "",
		"mobile_no": "",
		"last_reply_by": "",
		"last_reply_by_user": "",
		"conversation_start_at": "",
		"last_reply_at": "",
		"whatsapp_message_templates": [],
		"alert": 0,
		"alert_by": "",
		"status": [],
		"taggings": []
	})

	for lead in leads:
		leads_defaultdict[lead.name]["name"] = lead.name
		leads_defaultdict[lead.name]["lead_name"] = lead.lead_name
		leads_defaultdict[lead.name]["mobile_no"] = lead.mobile_no
		leads_defaultdict[lead.name]["last_reply_by"] = lead.last_reply_by
		leads_defaultdict[lead.name]["last_reply_by_user"] = lead.last_reply_by_user
		leads_defaultdict[lead.name]["conversation_start_at"] = lead.conversation_start_at
		leads_defaultdict[lead.name]["last_reply_at"] = lead.last_reply_at
		leads_defaultdict[lead.name]["alert"] = lead.alert
		leads_defaultdict[lead.name]["alert_by"] = lead.alert_by
		if lead.whatsapp_message_templates not in leads_defaultdict[lead.name]["whatsapp_message_templates"]:
			leads_defaultdict[lead.name]["whatsapp_message_templates"].append(lead.whatsapp_message_templates)
		if lead.cla_status not in leads_defaultdict[lead.name]["status"]:
			leads_defaultdict[lead.name]["status"].append(lead.cla_status)
		if lead.tagging not in leads_defaultdict[lead.name]["taggings"]:
			leads_defaultdict[lead.name]["taggings"].append(lead.tagging)

	leads = leads_defaultdict.values()

	return leads

@frappe.whitelist()
def acceptConversation(crm_lead_name):
	crm_lead_assignments = frappe.db.get_list("CRM Lead Assignment", filters={"crm_lead": crm_lead_name}, pluck="name")
	for crm_lead_assignment in crm_lead_assignments:
		frappe.db.set_value("CRM Lead Assignment", crm_lead_assignment, {
			"status": "Accepted",
			"accepted_by": frappe.session.user
		})
	frappe.db.commit()
	frappe.publish_realtime("new_leads", {"accepted_lead": crm_lead_name, "user": frappe.session.user})

@frappe.whitelist()
def completeConversation(crm_lead_name, mark_as_close=False):
	if mark_as_close:
		frappe.get_doc({
			"doctype": "WhatsApp Close Log",
			"close_by": frappe.session.user,
			"crm_lead": crm_lead_name,
		}).insert(ignore_permissions=True)
	crm_lead_assignments = frappe.db.get_list("CRM Lead Assignment", filters={"crm_lead": crm_lead_name}, pluck="name")
	for crm_lead_assignment in crm_lead_assignments:
		frappe.db.set_value("CRM Lead Assignment", crm_lead_assignment, {
			"status": "Case Closed" if mark_as_close else "Completed",
			"accepted_by": None
		})
	frappe.db.set_value("CRM Lead", crm_lead_name, {
		"alert": 0,
		"alert_by": None
	})
	frappe.db.commit()
	crm_lead_assignments = frappe.db.get_all("CRM Lead Assignment", filters={"crm_lead": crm_lead_name}, fields=["name", "status"])
	unclosed_crm_lead_assignments = [crm_lead_assignment for crm_lead_assignment in crm_lead_assignments if crm_lead_assignment.status != "Case Closed"]
	if not unclosed_crm_lead_assignments:
		frappe.db.set_value("CRM Lead", crm_lead_name, {
			"closed": 1
		})
		frappe.db.commit()
	frappe.publish_realtime("new_leads", {})

@frappe.whitelist()
def tagConversation(crm_lead_name, tagging):
	create_crm_tagging_assignment(crm_lead_name, tagging)
	frappe.db.commit()
	frappe.publish_realtime("new_leads", {})

@frappe.whitelist()
def assignConversation(args=None, *, ignore_permissions=False):
	"""add in someone's to do list
	args = {
	        "assign_to": [],
	        "doctype": ,
	        "name": ,
	        "description": ,
	        "assignment_rule":
	}

	"""
	if not args:
		args = frappe.local.form_dict

	frappe.db.delete("CRM Lead Assignment", filters={"crm_lead": args["name"]})

	assignees = frappe.parse_json(args.get("assign_to"))

	assignees = [assignee["name"] for assignee in assignees]

	for assignee in assignees:
		if assignee == "Booking Centre":
			create_crm_lead_assignment(args["name"], "BookingHL", "New")
		else:
			assigned_templates = frappe.db.get_all("User Permission", filters={"user": assignee, "allow": "WhatsApp Message Templates"}, pluck="for_value", limit=1)
			if assigned_templates:
				create_crm_lead_assignment(args["name"], assigned_templates[0], "New")

	frappe.publish_realtime("new_leads", {})

@frappe.whitelist()
def unassignConversation(doctype, name, assign_to, ignore_permissions=False):
	if assign_to == "Booking Centre":
		assigned_templates = frappe.db.get_all("User Permission", filters={"user": "booking_centre_1@example.com", "allow": "WhatsApp Message Templates"}, pluck="for_value")
	else:
		assigned_templates = frappe.db.get_all("User Permission", filters={"user": assign_to, "allow": "WhatsApp Message Templates"}, pluck="for_value")
	frappe.db.delete("CRM Lead Assignment", filters={"crm_lead": name, "whatsapp_message_templates": ["in", assigned_templates]})
	frappe.publish_realtime("new_leads", {})

@frappe.whitelist()
def alertConversation(crm_lead_name):
	if frappe.db.get_value("CRM Lead", crm_lead_name, "alert"):
		frappe.db.set_value("CRM Lead", crm_lead_name, {
			"alert": 0,
			"alert_by": None
		})
		frappe.publish_realtime("new_leads", {})
		return

	username = frappe.db.get_value("User", frappe.session.user, "username")
	frappe.db.set_value("CRM Lead", crm_lead_name, {
		"alert": 1,
		"alert_by": username
	})

	send_push_notification_to_crm_admin("Alert! : by {0}".format(username), "Alert! A conversation requires your attention!", get_users_with_crm_admin_role(), "https://crm.techmind.com.my/crm/leads/{0}?viewType=#whatsapp".format(crm_lead_name))

	frappe.publish_realtime("new_leads", {})

def get_users_with_crm_admin_role():
	users = get_users_with_role("CRM Admin")

	if not users:
		users = []
	
	return users

def send_push_notification_to_crm_admin(title, message, users, url=None):
	if not users:
		return
	push_notification_subscriptions = frappe.db.get_all("Push Notification Subscription", filters={"user": ["in", users]}, pluck="name")
	for push_notification_subscription in push_notification_subscriptions:
		push_notification = frappe.new_doc("Push Notification Log")
		push_notification.push_notification_subscription = push_notification_subscription
		push_notification.title = title
		push_notification.message = message
		push_notification.url = url
		push_notification.insert(ignore_permissions=True)