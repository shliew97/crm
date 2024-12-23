# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ClockInandClockOut(Document):
	@staticmethod
	def default_list_data():
		rows = [
			"name",
			"record_type",
			"datetime",
			"user",
			"owner",
			"modified",
		]
		return {'columns': [], 'rows': rows}

	def before_insert(self):
		self.user = frappe.session.user
		latest_clock_in_out = frappe.db.get_all("Clock In and Clock Out", filters={"user": frappe.session.user}, order_by="creation desc", fields=["record_type"], limit=1)
		if latest_clock_in_out:
			self.record_type = "Out" if latest_clock_in_out[0].record_type == "In" else "In"
		else:
			self.record_type == "In"