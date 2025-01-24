import frappe
from frappe import _

from crm.api.doc import get_fields_meta, get_assigned_users
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script

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
	return lead

@frappe.whitelist()
def get_new_leads():
	Lead = frappe.qb.DocType("CRM Lead")

	conditions = ((Lead.conversation_status == "New") | ((Lead.conversation_status == "Accepted") & (Lead.accepted_by_user == frappe.session.user)))
	query = frappe.qb.from_(Lead).select("*").where(conditions).orderby(Lead.modified, order=frappe.qb.desc)

	leads = query.run(as_dict=True)

	if not leads:
		leads = []

	return leads

@frappe.whitelist()
def acceptConversation(crm_lead_name):
	frappe.db.set_value("CRM Lead", crm_lead_name, {
		"conversation_status": "Accepted",
		"accepted_by_user": frappe.session.user
	})
	frappe.db.commit()
	frappe.publish_realtime("new_leads", {})

@frappe.whitelist()
def completeConversation(crm_lead_name):
	frappe.db.set_value("CRM Lead", crm_lead_name, {
		"conversation_status": "Completed",
		"accepted_by_user": None
	})
	frappe.db.commit()
	frappe.publish_realtime("new_leads", {})