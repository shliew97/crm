import frappe
from frappe import _

from crm.api.doc import get_fields_meta, get_assigned_users
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script
from collections import defaultdict
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.whatsapp_message import create_crm_tagging_assignment, create_crm_lead_assignment

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
	lead["_assignments"] = frappe.db.get_list("CRM Lead Assignment", pluck="status")
	return lead

@frappe.whitelist()
def get_new_leads(search_text=None):
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
			ORDER BY FIELD(cla.status, 'New', 'Accepted', 'Completed', 'Case Closed'), cl.last_reply_at DESC
		""", as_dict=1)
	elif "CRM Agent" in user_roles and "System Manager" not in user_roles:
		crm_lead_assignments = frappe.db.get_list("CRM Lead Assignment", pluck="name")

		values = {
			"user": frappe.session.user,
			"crm_lead_assignments": tuple(crm_lead_assignments),
		}

		leads = frappe.db.sql("""
			SELECT
				cl.*, cla.status AS cla_status, clt.tagging
			FROM `tabCRM Lead` cl
			JOIN `tabCRM Lead Assignment` cla
			ON cl.name = cla.crm_lead
			LEFT JOIN `tabCRM Lead Tagging` clt
			ON cl.name = clt.crm_lead AND clt.status = "Open"
			WHERE cla.status IN ("New", "Accepted", "Completed")
			AND cla.name IN %(crm_lead_assignments)s
			ORDER BY FIELD(cla.status, 'New', 'Accepted', 'Completed', 'Case Closed'), cl.last_reply_at DESC
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
			WHERE cla.status IN ("New", "Accepted", "Completed")
			ORDER BY FIELD(cla.status, 'New', 'Accepted', 'Completed', 'Case Closed'), cl.last_reply_at DESC
		""", values=values, as_dict=1)

	if not leads:
		leads = []

	leads_defaultdict = defaultdict(lambda: {
		"name": "",
		"lead_name": "",
		"mobile_no": "",
		"last_reply_by": "",
		"last_reply_at": "",
		"whatsapp_message_templates": [],
		"status": [],
		"taggings": []
	})

	for lead in leads:
		leads_defaultdict[lead.name]["name"] = lead.name
		leads_defaultdict[lead.name]["lead_name"] = lead.lead_name
		leads_defaultdict[lead.name]["mobile_no"] = lead.mobile_no
		leads_defaultdict[lead.name]["last_reply_by"] = lead.last_reply_by
		leads_defaultdict[lead.name]["last_reply_at"] = lead.last_reply_at
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
		frappe.db.set_value("CRM Lead Assignment", crm_lead_assignment, "status", "Accepted")
	frappe.db.commit()
	frappe.publish_realtime("new_leads", {})

@frappe.whitelist()
def completeConversation(crm_lead_name):
	crm_lead_assignments = frappe.db.get_list("CRM Lead Assignment", filters={"crm_lead": crm_lead_name}, pluck="name")
	for crm_lead_assignment in crm_lead_assignments:
		frappe.db.set_value("CRM Lead Assignment", crm_lead_assignment, "status", "Completed")
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

	for assign_to in frappe.parse_json(args.get("assign_to")):
		assigned_templates = frappe.db.get_all("User Permission", filters={"user": assign_to, "allow": "WhatsApp Message Templates"}, pluck="for_value", limit=1)
		if assigned_templates:
			create_crm_lead_assignment(args["name"], assigned_templates[0], "New")

	frappe.publish_realtime("new_leads", {})

@frappe.whitelist()
def unassignConversation(doctype, name, assign_to, ignore_permissions=False):
	assigned_templates = frappe.db.get_all("User Permission", filters={"user": assign_to, "allow": "WhatsApp Message Templates"}, pluck="for_value")
	frappe.db.delete("CRM Lead Assignment", filters={"crm_lead": name, "whatsapp_message_templates": ["in", assigned_templates]})
	frappe.publish_realtime("new_leads", {})