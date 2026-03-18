import frappe
from frappe.utils import get_datetime

def expire_slot_suggestions():
    slot_suggestions = frappe.db.get_all("Slot Suggestions", filters={"expired": 0}, fields=["name", "expires_at"])

    current_datetime = get_datetime()

    for slot_suggestion in slot_suggestions:
        if slot_suggestion.expires_at < current_datetime:
            frappe.db.set_value("Slot Suggestions", slot_suggestion.name, "expired", 1)