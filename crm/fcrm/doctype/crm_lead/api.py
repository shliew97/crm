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
	user_roles = frappe.get_roles()

	if "CRM Agent" in user_roles and "System Manager" not in user_roles:
		whatsapp_message_templates = frappe.db.get_list("WhatsApp Message Templates", pluck="name")

		values = {
			"user": frappe.session.user,
			"whatsapp_message_templates": tuple(whatsapp_message_templates),
		}

		leads = frappe.db.sql("""
			SELECT
				*
			FROM `tabCRM Lead` cl
			WHERE (cl.conversation_status = "New" OR (cl.conversation_status = "Accepted" AND cl.accepted_by_user = %(user)s))
			AND cl.whatsapp_message_templates IN %(whatsapp_message_templates)s
			ORDER BY cl.modified DESC
		""", values=values, as_dict=1)

		shared_leads = frappe.db.sql("""
			SELECT
				*
			FROM `tabCRM Lead` cl
			JOIN `tabDocShare` ds
			ON ds.share_name = cl.name
			WHERE (cl.conversation_status = "New" OR (cl.conversation_status = "Accepted" AND cl.accepted_by_user = %(user)s))
			AND ds.share_doctype = "CRM Lead"
			AND ds.user = %(user)s
			ORDER BY cl.modified DESC
		""", values=values, as_dict=1)

		leads += shared_leads
	else:
		values = {
			"user": frappe.session.user,
		}

		leads = frappe.db.sql("""
			SELECT
				*
			FROM `tabCRM Lead` cl
			WHERE (cl.conversation_status = "New" OR (cl.conversation_status = "Accepted" AND cl.accepted_by_user = %(user)s))
			ORDER BY cl.modified DESC
		""", values=values, as_dict=1)

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

@frappe.whitelist()
def tagConversation(crm_lead_name, tagging):
	frappe.db.set_value("CRM Lead", crm_lead_name, {
		"tagging": tagging
	})
	frappe.db.commit()
	frappe.publish_realtime("new_leads", {})

@frappe.whitelist()
def assignConversation(crm_lead_name, user):
	frappe.share.add_docshare(
		"CRM Lead", crm_lead_name, user, read=1, write=1, flags={"ignore_share_permission": True}
	)
	frappe.publish_realtime("new_leads", {})