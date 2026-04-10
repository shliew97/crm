import frappe
import json
import requests
from frappe import _
from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
from frappe.utils.user import get_users_with_role
from frappe.utils import get_datetime, add_to_date

def validate(doc, method):
    if doc.type == "Incoming" and doc.get("from"):
        name, doctype = get_lead_or_deal_from_number(doc.get("from"))
        if not name:
            crm_lead_doc = frappe.new_doc("CRM Lead")
            crm_lead_doc.first_name = doc.from_name or ""
            crm_lead_doc.last_name = ""
            crm_lead_doc.mobile_no = doc.get("from")
            crm_lead_doc.insert(ignore_permissions=True)
            name = crm_lead_doc.name
        doc.reference_doctype = doctype
        doc.reference_name = name


def on_update(doc, method):
    if not doc.get_doc_before_save():
        frappe.publish_realtime(
            "whatsapp_message",
            {
                "reference_doctype": doc.reference_doctype,
                "reference_name": doc.reference_name,
            },
        )
    # if not doc.flags.is_template_queue:
    #     frappe.publish_realtime("new_leads", {})

    notify_agent(doc)


def notify_agent(doc):
    if doc.type == "Incoming":
        doctype = doc.reference_doctype
        if doctype.startswith("CRM "):
            doctype = doctype[4:].lower()
        notification_text = f"""
            <div class="mb-2 leading-5 text-gray-600">
                <span class="font-medium text-gray-900">{ _('You') }</span>
                <span>{ _('received a whatsapp message in {0}').format(doctype) }</span>
                <span class="font-medium text-gray-900">{ doc.reference_name }</span>
            </div>
        """
        assigned_users = get_assigned_users(doc.reference_doctype, doc.reference_name)
        for user in assigned_users:
            notify_user({
                "owner": doc.owner,
                "assigned_to": user,
                "notification_type": "WhatsApp",
                "message": doc.message,
                "notification_text": notification_text,
                "reference_doctype": "WhatsApp Message",
                "reference_docname": doc.name,
                "redirect_to_doctype": doc.reference_doctype,
                "redirect_to_docname": doc.reference_name,
            })


def get_lead_or_deal_from_number(number):
    """Get lead/deal from the given number."""

    def find_record(doctype, mobile_no, where=""):
        mobile_no = parse_mobile_no(mobile_no)

        query = f"""
            SELECT name, mobile_no
            FROM `tab{doctype}`
            WHERE CONCAT('+', REGEXP_REPLACE(mobile_no, '[^0-9]', '')) = {mobile_no}
        """

        data = frappe.db.sql(query + where, as_dict=True)
        return data[0].name if data else None

    doctype = "CRM Deal"

    doc = find_record(doctype, number) or None
    if not doc:
        doctype = "CRM Lead"
        doc = find_record(doctype, number, "AND converted is not True")
        if not doc:
            doc = find_record(doctype, number)

    return doc, doctype


def parse_mobile_no(mobile_no: str):
    """Parse mobile number to remove spaces, brackets, etc.
    >>> parse_mobile_no('+91 (766) 667 6666')
    ... '+917666676666'
    """
    return "".join([c for c in mobile_no if c.isdigit() or c == "+"])


@frappe.whitelist()
def is_whatsapp_enabled():
    if not frappe.db.exists("DocType", "WhatsApp Settings"):
        return False
    return frappe.get_cached_value("WhatsApp Settings", "WhatsApp Settings", "enabled")

@frappe.whitelist()
def is_whatsapp_installed():
    if not frappe.db.exists("DocType", "WhatsApp Settings"):
        return False
    return True

@frappe.whitelist()
def is_master_agent():
    user_roles = frappe.get_roles()
    if "Master Agent" in user_roles:
        return True
    return False

@frappe.whitelist()
def is_master_agent_and_booking_centre():
    response = {
        "is_master_agent": False,
        "is_booking_centre": False,
        "is_booking_centre_master_ai": False,
    }
    user_roles = frappe.get_roles()
    if "Master Agent" in user_roles:
        response ["is_master_agent"] = True
    if "Booking Centre" in user_roles:
        response ["is_booking_centre"] = True
    if "Booking Centre Master AI" in user_roles:
        response ["is_booking_centre_master_ai"] = True
    return response

@frappe.whitelist()
def suggest_next_action(reference_doctype, reference_name):
    """Call LLM to suggest next action for the agent based on conversation context."""
    if "Booking Centre Master AI" not in frappe.get_roles():
        frappe.throw("Not permitted", frappe.PermissionError)

    from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.ai_utils import suggest_next_action as _suggest
    result = _suggest(reference_doctype, reference_name)

    # Attach the last incoming message for AI logging
    last_incoming = frappe.db.get_value(
        "WhatsApp Message",
        filters={
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "type": "Incoming",
        },
        fieldname="message",
        order_by="timestamp desc",
    )
    if isinstance(result, dict):
        result["last_incoming_message"] = last_incoming or ""
    else:
        result = {"suggestion": result, "last_incoming_message": last_incoming or ""}

    return result

@frappe.whitelist()
def log_booking_centre_ai(message, ai_suggested_reply, final_reply):
    """Log the AI suggestion and final reply to Booking Centre AI Log."""
    frappe.get_doc({
        "doctype": "Booking Centre AI Log",
        "message": message,
        "ai_generated_reply": ai_suggested_reply,
        "final_reply": final_reply,
    }).insert(ignore_permissions=True)
    return {"ok": True}

@frappe.whitelist()
def cancel_pending_action(reference_doctype, reference_name):
    """Clear awaiting flags from pending booking data when agent cancels a popup."""
    if "Booking Centre Master AI" not in frappe.get_roles():
        frappe.throw("Not permitted", frappe.PermissionError)

    from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.agents.rag_chain import (
        get_pending_booking_data, save_pending_booking_data
    )

    lead_doc = frappe.get_doc(reference_doctype, reference_name)
    pending_data = get_pending_booking_data(lead_doc)
    if not pending_data:
        return {"ok": True}

    # Clear all awaiting flags and related temp data
    awaiting_keys = [k for k in pending_data if k.startswith("awaiting_")]
    for k in awaiting_keys:
        pending_data[k] = False

    # Clean up temp fields from create booking flow
    pending_data.pop('outlet_ambiguous', None)
    pending_data.pop('outlet_possible_matches', None)
    pending_data.pop('outlet_original_input', None)
    pending_data.pop('outlet_matched_name', None)
    pending_data.pop('outlet_matched_branch_code', None)
    pending_data.pop('suggested_slot_1', None)
    pending_data.pop('suggested_slot_2', None)
    pending_data.pop('numbered_slots', None)
    # Clean up temp fields from update flow
    pending_data.pop('pending_update_fields', None)
    pending_data.pop('fetched_bookings_map', None)
    # Clean up temp fields from delete flow
    pending_data.pop('delete_order_ids', None)
    pending_data.pop('delete_booking_summary', None)
    pending_data.pop('fetched_delete_bookings_map', None)

    save_pending_booking_data(lead_doc, pending_data)
    return {"ok": True}

@frappe.whitelist()
def get_users_with_crm_assignee_role():
    users = get_users_with_role("CRM Assignee")

    users = frappe.db.get_all("User", filters={"name": ["in", users]}, fields=["name", "first_name"])

    users = [{"value": user.name, "description": user.first_name} for user in users if user.name != "Administrator"]

    users.append({"value": "Booking Centre", "description": "Booking Centre"})

    if not users:
        users = []
    
    return users

@frappe.whitelist()
def get_crm_assignees(crm_lead):
    bc_users = get_users_with_role("Booking Centre")
    existing_templates = frappe.db.get_all("CRM Lead Assignment", filters={"crm_lead": crm_lead, "status": ["in", ["New", "Accepted"]]}, pluck="whatsapp_message_templates")
    users_with_permission = frappe.db.get_all("User Permission", filters={"allow": "WhatsApp Message Templates", "for_value": ["in", existing_templates]}, pluck="user")

    users = frappe.db.get_all("User", filters={"name": ["in", users_with_permission]}, fields=["name", "first_name"])

    crm_assignees = [{"name": user.name, "label": user.first_name[0], "has_bc_role": user.name in bc_users} for user in users]

    if not crm_assignees:
        crm_assignees = []
    
    return crm_assignees

@frappe.whitelist()
def get_whatsapp_messages(reference_doctype, reference_name, limit=88):
    if not frappe.db.exists("DocType", "WhatsApp Message"):
        return []
    limit = int(limit)
    messages = []

    if reference_doctype == 'CRM Deal':
        lead = frappe.db.get_value(reference_doctype, reference_name, 'lead')
        if lead:
            messages = frappe.get_all(
                "WhatsApp Message",
                filters={
                    "reference_doctype": "CRM Lead",
                    "reference_name": lead,
                },
                fields=[
                    "name",
                    "type",
                    "to",
                    "from",
                    "content_type",
                    "message_type",
                    "attach",
                    "template",
                    "use_template",
                    "message_id",
                    "is_reply",
                    "is_forwarded",
                    "reply_to_message_id",
                    "timestamp",
                    "message",
                    "status",
                    "reference_doctype",
                    "reference_name",
                    "template_parameters",
                    "template_header_parameters",
                    "owner",
                ],
                limit=limit,
                order_by="timestamp desc",
            )

    messages += frappe.get_all(
        "WhatsApp Message",
        filters={
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
        },
        fields=[
            "name",
            "type",
            "to",
            "from",
            "content_type",
            "message_type",
            "attach",
            "template",
            "use_template",
            "message_id",
            "is_reply",
            "is_forwarded",
            "reply_to_message_id",
            "timestamp",
            "message",
            "status",
            "reference_doctype",
            "reference_name",
            "template_parameters",
            "template_header_parameters",
            "owner",
        ],
        limit=limit,
        order_by="timestamp desc",
    )

    # Filter messages to get only Template messages
    template_messages = [
        message for message in messages if message["message_type"] == "Template"
    ]

    # Iterate through template messages
    for template_message in template_messages:
        # Find the template that this message is using
        template = frappe.get_doc("WhatsApp Templates", template_message["template"])

        # If the template is found, add the template details to the template message
        if template:
            template_message["template_name"] = template.template_name
            if template_message["template_parameters"]:
                parameters = json.loads(template_message["template_parameters"])
                template.template = parse_template_parameters(
                    template.template, parameters
                )

            template_message["template"] = template.template
            if template_message["template_header_parameters"]:
                header_parameters = json.loads(
                    template_message["template_header_parameters"]
                )
                template.header = parse_template_parameters(
                    template.header, header_parameters
                )
            template_message["header"] = template.header
            template_message["footer"] = template.footer

    # Filter messages to get only reaction messages
    reaction_messages = [
        message for message in messages if message["content_type"] == "reaction"
    ]

    # Iterate through reaction messages
    for reaction_message in reaction_messages:
        # Find the message that this reaction is reacting to
        reacted_message = next(
            (
                m
                for m in messages
                if m["message_id"] == reaction_message["reply_to_message_id"]
            ),
            None,
        )

        # If the reacted message is found, add the reaction to it
        if reacted_message:
            reacted_message["reaction"] = reaction_message["message"]

    for message in messages:
        from_name = get_from_name(message) if message["from"] else _("You")
        message["from_name"] = from_name
    # Filter messages to get only replies
    reply_messages = [message for message in messages if message["is_reply"]]

    # Iterate through reply messages
    for reply_message in reply_messages:
        # Find the message that this message is replying to
        replied_message = next(
            (
                m
                for m in messages
                if m["message_id"] == reply_message["reply_to_message_id"]
            ),
            None,
        )

        # If the replied message is found, add the reply details to the reply message
        if replied_message:
            from_name = (
                get_from_name(reply_message) if replied_message["from"] else _("You")
            )

            message = replied_message["message"]
            if replied_message["message_type"] == "Template":
                message = replied_message["template"]
            reply_message["reply_message"] = message
            reply_message["header"] = replied_message.get("header") or ""
            reply_message["footer"] = replied_message.get("footer") or ""
            reply_message["reply_to"] = replied_message["name"]
            reply_message["reply_to_type"] = replied_message["type"]
            reply_message["reply_to_from"] = from_name

    messages = [message for message in messages if message["content_type"] != "reaction"]

    # Fetch Pending WhatsApp Messages (Pending and Expired)
    pending_messages = frappe.get_all(
        "Pending WhatsApp Message",
        filters={
            "status": ["in", ["Pending", "Expired"]],
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
        },
        fields=[
            "name",
            "type",
            "to",
            "`from`",
            "content_type",
            "message_type",
            "attach",
            "message",
            "status",
            "timestamp",
            "reference_doctype",
            "reference_name",
            "owner",
        ],
        order_by="creation asc",
    )

    for pm in pending_messages:
        pm["is_pending_whatsapp_message"] = True
        pm["pending_status"] = pm["status"]
        # Set fields expected by the frontend
        pm["message_id"] = ""
        pm["is_reply"] = 0
        pm["is_forwarded"] = 0
        pm["reply_to_message_id"] = ""
        pm["use_template"] = 0
        pm["template"] = ""
        pm["template_parameters"] = ""
        pm["template_header_parameters"] = ""
        if not pm.get("type"):
            pm["type"] = "Outgoing"

    messages.extend(pending_messages)

    return messages


@frappe.whitelist()
def create_whatsapp_message(
    reference_doctype,
    reference_name,
    message,
    to,
    attach,
    reply_to,
    content_type="text",
):
    doc = frappe.new_doc("WhatsApp Message")

    if reply_to:
        reply_doc = frappe.get_doc("WhatsApp Message", reply_to)
        doc.update(
            {
                "is_reply": True,
                "reply_to_message_id": reply_doc.message_id,
            }
        )

    doc.update(
        {
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "message": message or attach,
            "to": to,
            "attach": attach,
            "content_type": content_type,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def send_whatsapp_template(reference_doctype, reference_name, template, to):
    whatsapp_template_doc = frappe.get_doc("WhatsApp Templates", template)
    doc = frappe.new_doc("WhatsApp Message")
    doc.update(
        {
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "message_type": "Manual",
            "message": whatsapp_template_doc.template,
            "content_type": "text",
            "to": to,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def react_on_whatsapp_message(emoji, reply_to_name):
    reply_to_doc = frappe.get_doc("WhatsApp Message", reply_to_name)
    to = reply_to_doc.type == "Incoming" and reply_to_doc.get("from") or reply_to_doc.to
    doc = frappe.new_doc("WhatsApp Message")
    doc.update(
        {
            "reference_doctype": reply_to_doc.reference_doctype,
            "reference_name": reply_to_doc.reference_name,
            "message": emoji,
            "to": to,
            "reply_to_message_id": reply_to_doc.message_id,
            "content_type": "reaction",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def retry_pending_whatsapp_message(name):
    frappe.db.set_value("Pending WhatsApp Message", name, "status", "Pending")
    return "ok"


def parse_template_parameters(string, parameters):
    for i, parameter in enumerate(parameters, start=1):
        placeholder = "{{" + str(i) + "}}"
        string = string.replace(placeholder, parameter)

    return string


def get_from_name(message):
    doc = frappe.get_doc(message["reference_doctype"], message["reference_name"])
    from_name = ""
    if message["reference_doctype"] == "CRM Deal":
        if doc.get("contacts"):
            for c in doc.get("contacts"):
                if c.is_primary:
                    from_name = c.full_name or c.mobile_no
                    break
        else:
            from_name = doc.get("lead_name")
    else:
        from_name = doc.get("first_name") + " " + doc.get("last_name")
    return from_name

@frappe.whitelist()
def get_username():
    return frappe.db.get_value("User", frappe.session.user, "username")


@frappe.whitelist()
def create_booking(crm_lead, booking_details, message, booking_info_with_regex, booking_info):
    frappe.get_doc({
        "doctype": "Booking Log",
        "message": message,
        "booking_info_with_regex": booking_info_with_regex,
        "booking_info": booking_info,
    }).insert(ignore_permissions=True)

    frappe.db.commit()

    if isinstance(booking_details, str):
        booking_details = json.loads(booking_details)

    # combine date and time
    booking_datetime = get_datetime(f'{booking_details["booking_date"]} {booking_details["timeslot"]}')

    # check if overed
    if get_datetime() > booking_datetime:
        return {
            "success": False,
            "message": "Booking date and time was already overed.",
        }

    # Format timeslot if needed (e.g. "1430" -> "14:30:00")
    timeslot = booking_details.get("timeslot", "")
    if timeslot and ":" not in str(timeslot):
        timeslot = str(timeslot)
        if len(timeslot) == 4:
            booking_details["timeslot"] = timeslot[:2] + ":" + timeslot[2:] + ":00"

    outlets = frappe.db.get_all("Outlet", filters={"name": booking_details.get("outlet")}, fields=["name", "integration_settings"])

    if not outlets:
        return {
            "success": False,
            "message": "Outlet not available for booking.",
        }

    integration_settings_doc = frappe.get_doc("Integration Settings", outlets[0].integration_settings)
    url = integration_settings_doc.site_url + "/api/method/healthland_pos.booking.crm_make_bookings"

    headers = {
        "Authorization": "Basic {0}".format(integration_settings_doc.get_password("access_token")),
        "Content-Type": "application/json"
    }

    request_payload = json.dumps(booking_details, default=str)
    response = requests.post(url, data=request_payload, headers=headers, timeout=30)
    response.raise_for_status()

    response_json = response.json()

    if response_json["success"] == False:
        update_slot_suggestions(
            crm_lead,
            json.dumps(response_json["suggested_slot_1"]),
            response_json["suggested_slot_message_1"],
            json.dumps(response_json["suggested_slot_2"]),
            json.dumps(response_json["suggested_slot_3"]),
            response_json["suggested_slot_message_3"],
            json.dumps(response_json["suggested_slot_4"]),
            json.dumps(response_json["suggested_slot_5"]),
            response_json["suggested_slot_message_5"],
            json.dumps(response_json["suggested_slot_6"]),
            response_json["member_mobile"],
            response_json["pax"],
            response_json["treatment"],
            response_json["session"],
            response_json["preferred_therapist"],
            response_json["third_party_voucher"],
            response_json["package"],
        )

    return response_json


@frappe.whitelist()
def edit_booking(order_ids, booking_details):
    if isinstance(booking_details, str):
        booking_details = json.loads(booking_details)

    # combine date and time
    booking_datetime = get_datetime(f'{booking_details["booking_date"]} {booking_details["timeslot"]}')

    # check if overed
    if get_datetime() > booking_datetime:
        return {
            "success": False,
            "message": "Booking date and time was already overed.",
        }

    # Only allow permitted fields
    allowed_fields = {"booking_date", "timeslot", "treatment", "session", "preferred_therapist", "third_party_voucher", "package"}
    booking_details = {k: v for k, v in booking_details.items() if k in allowed_fields}

    # Format timeslot to HH:MM:SS
    timeslot = booking_details.get("timeslot", "")
    if timeslot:
        timeslot = str(timeslot)
        if ":" not in timeslot and len(timeslot) == 4:
            # e.g. "1500" -> "15:00:00"
            booking_details["timeslot"] = timeslot[:2] + ":" + timeslot[2:] + ":00"
        elif timeslot.count(":") == 1:
            # e.g. "15:00" -> "15:00:00"
            booking_details["timeslot"] = timeslot + ":00"

    booking_details["order_ids"] = json.dumps(order_ids) if isinstance(order_ids, list) else order_ids

    integration_settings = frappe.db.get_all("Integration Settings", filters={"integration_type": "ERP"}, pluck="name")
    for integration_setting in integration_settings:
        integration_settings_doc = frappe.get_doc("Integration Settings", integration_setting)
        url = integration_settings_doc.site_url + "/api/method/healthland_pos.booking.crm_update_bookings"

        headers = {
            "Authorization": "Basic {0}".format(integration_settings_doc.get_password("access_token")),
            "Content-Type": "application/json"
        }

        payload = json.dumps(booking_details, default=str)
        frappe.log_error("edit_booking Request", f"URL: {url}\nPayload: {payload}")
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        frappe.log_error("edit_booking Response", f"Status: {response.status_code}\nBody: {response.text}")
        response.raise_for_status()
        return response.json()


@frappe.whitelist()
def delete_booking(order_ids):
    integration_settings = frappe.db.get_all("Integration Settings", filters={"integration_type": "ERP"}, pluck="name")
    for integration_setting in integration_settings:
        integration_settings_doc = frappe.get_doc("Integration Settings", integration_setting)
        url = integration_settings_doc.site_url + "/api/method/healthland_pos.booking.crm_delete_bookings"

        headers = {
            "Authorization": "Basic {0}".format(integration_settings_doc.get_password("access_token")),
            "Content-Type": "application/json"
        }

        payload = {
            "order_ids": json.dumps(order_ids) if isinstance(order_ids, list) else order_ids
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()


@frappe.whitelist()
def get_customer_membership_and_balance(outlet, member_mobile):
    integration_settings = frappe.db.get_all("Integration Settings", filters={"integration_type": "ERP"}, pluck="name")
    for integration_setting in integration_settings:
        integration_settings_doc = frappe.get_doc("Integration Settings", integration_setting)
        url = integration_settings_doc.site_url + "/api/method/healthland_pos.booking.crm_get_customer_membership_and_balance"

        headers = {
            "Authorization": "Basic {0}".format(integration_settings_doc.get_password("access_token")),
            "Content-Type": "application/json"
        }

        payload = {
            "outlet": outlet,
            "member_mobile": member_mobile
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    return {}


@frappe.whitelist()
def fetch_bookings(booking_mobile):
    message_data = {"bookings": []}
    integration_settings = frappe.db.get_all("Integration Settings", filters={"integration_type": "Outlet Sync"}, pluck="name")
    for integration_setting in integration_settings:
        integration_settings_doc = frappe.get_doc("Integration Settings", integration_setting)
        url = integration_settings_doc.site_url + "/api/method/healthland_pos.booking.crm_fetch_bookings"

        headers = {
            "Authorization": "Basic {0}".format(integration_settings_doc.get_password("access_token")),
            "Content-Type": "application/json"
        }

        payload = {
            "booking_mobile": booking_mobile
        }

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()

            bookings = result.get("bookings", [])

            for booking in bookings:
                booking["integration_settings"] = integration_setting

            message_data["bookings"] += bookings
        except Exception as e:
            frappe.log_error("Fetch Bookings Error", f"Error fetching bookings for {booking_mobile}: {str(e)}\n{frappe.get_traceback()}")
            return {"bookings": []}

    return message_data

def update_slot_suggestions(
    crm_lead,
    suggested_slot_1,
    suggested_slot_message_1,
    suggested_slot_2,
    suggested_slot_3,
    suggested_slot_message_3,
    suggested_slot_4,
    suggested_slot_5,
    suggested_slot_message_5,
    suggested_slot_6,
    member_mobile,
    pax,
    treatment,
    session,
    preferred_therapist,
    third_party_voucher,
    package,
):
    slot_suggestions = frappe.db.get_all("Slot Suggestions", filters={"reference_name": crm_lead}, pluck="name")

    if not slot_suggestions:
        slot_suggestion_doc = frappe.get_doc({
            "doctype": "Slot Suggestions",
            "reference_name": crm_lead,
            "expires_at": add_to_date(get_datetime(), hours=48)
        })
    else:
        slot_suggestion_doc = frappe.get_doc("Slot Suggestions", slot_suggestions[0])
        slot_suggestion_doc.expires_at = add_to_date(get_datetime(), hours=48)
        slot_suggestion_doc.expired = 0

    slot_suggestion_doc.suggested_slot_1 = suggested_slot_1
    slot_suggestion_doc.suggested_slot_message_1 = suggested_slot_message_1
    slot_suggestion_doc.suggested_slot_2 = suggested_slot_2
    slot_suggestion_doc.suggested_slot_3 = suggested_slot_3
    slot_suggestion_doc.suggested_slot_message_3 = suggested_slot_message_3
    slot_suggestion_doc.suggested_slot_4 = suggested_slot_4
    slot_suggestion_doc.suggested_slot_5 = suggested_slot_5
    slot_suggestion_doc.suggested_slot_message_5 = suggested_slot_message_5
    slot_suggestion_doc.suggested_slot_6 = suggested_slot_6
    slot_suggestion_doc.member_mobile = member_mobile
    slot_suggestion_doc.pax = pax
    slot_suggestion_doc.treatment = treatment
    slot_suggestion_doc.session = session
    slot_suggestion_doc.preferred_therapist = preferred_therapist
    slot_suggestion_doc.third_party_voucher = third_party_voucher
    slot_suggestion_doc.package = package
    slot_suggestion_doc.save(ignore_permissions=True)