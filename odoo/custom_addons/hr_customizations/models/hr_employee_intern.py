# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_intern_employee = fields.Boolean(
        string="Intern Employee",
        default=False,
        tracking=True,
        index=True,
        help="Enable this when the employee record belongs to an intern.",
    )

    intern_source = fields.Selection(
        selection=[
            ("manual", "Manual"),
            ("intern_recruitment", "Intern Recruitment"),
        ],
        string="Intern Source",
        default="manual",
        tracking=True,
        help="Indicates how the intern employee record was created.",
    )

    def action_convert_intern_to_employee(self):
        """
        Convert an existing intern into a regular employee.

        No duplicate hr.employee record is created. The existing record is
        converted by changing is_intern_employee from True to False.
        """
        self.ensure_one()

        if not self.active:
            raise UserError(
                _("An archived intern cannot be converted into an employee.")
            )

        if not self.is_intern_employee:
            raise UserError(
                _("This record is already a regular employee.")
            )

        if (
            "is_blacklisted_employee" in self._fields
            and self.is_blacklisted_employee
        ):
            raise UserError(
                _("A blacklisted intern cannot be converted into an employee.")
            )

        self.write(
            {
                "is_intern_employee": False,
            }
        )

        self.message_post(
            body=_(
                "The intern was converted into a regular employee. "
                "The existing employee record was retained."
            )
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Employee"),
            "res_model": "hr.employee",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
        }