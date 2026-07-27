# -*- coding: utf-8 -*-

from markupsafe import Markup

from odoo import fields, models, _
from odoo.exceptions import UserError


class HrEmployeeBlacklistReason(models.Model):
    _name = "hr.employee.blacklist.reason"
    _description = "Employee Blacklist Reason"
    _order = "sequence asc, name asc"

    name = fields.Char(
        string="Reason",
        required=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

    description = fields.Text(
        string="Description",
    )


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_blacklisted_employee = fields.Boolean(
        string="Blacklisted",
        default=False,
        tracking=True,
        copy=False,
    )

    blacklist_reason_id = fields.Many2one(
        "hr.employee.blacklist.reason",
        string="Blacklist Reason",
        tracking=True,
        copy=False,
    )

    blacklist_description = fields.Text(
        string="Blacklist Description",
        tracking=True,
        copy=False,
    )

    blacklist_date = fields.Datetime(
        string="Blacklisted On",
        readonly=True,
        copy=False,
    )

    blacklisted_by_id = fields.Many2one(
        "res.users",
        string="Blacklisted By",
        readonly=True,
        copy=False,
    )

    whitelist_date = fields.Datetime(
        string="Whitelisted On",
        readonly=True,
        copy=False,
    )

    whitelisted_by_id = fields.Many2one(
        "res.users",
        string="Whitelisted By",
        readonly=True,
        copy=False,
    )

    def action_open_blacklist_wizard(self):
        employees = self.filtered(lambda employee: not employee.is_blacklisted_employee)

        if not employees:
            raise UserError(_("Selected employee is already blacklisted."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Blacklist Employee"),
            "res_model": "hr.employee.blacklist.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_employee_ids": [(6, 0, employees.ids)],
            },
        }

    def action_whitelist_employee(self):
        employees = self.filtered(lambda employee: employee.is_blacklisted_employee)

        if not employees:
            raise UserError(_("Selected employee is not blacklisted."))

        employees.write(
            {
                "is_blacklisted_employee": False,
                "blacklist_reason_id": False,
                "blacklist_description": False,
                "blacklist_date": False,
                "blacklisted_by_id": False,
                "whitelist_date": fields.Datetime.now(),
                "whitelisted_by_id": self.env.user.id,

                # Whitelisted employees become active again.
                "active": True,
            }
        )

        for employee in employees:
            employee.message_post(
                body=_("Employee has been whitelisted by %s.") % self.env.user.name
            )

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }


class HrEmployeeBlacklistWizard(models.TransientModel):
    _name = "hr.employee.blacklist.wizard"
    _description = "Blacklist Employee Wizard"

    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employees",
        required=True,
    )

    reason_id = fields.Many2one(
        "hr.employee.blacklist.reason",
        string="Blacklist Reason",
        required=True,
    )

    description = fields.Text(
        string="Detailed Reason",
        required=True,
    )

    def action_confirm_blacklist(self):
        self.ensure_one()

        if not self.employee_ids:
            raise UserError(_("Please select at least one employee to blacklist."))

        self.employee_ids.write(
            {
                "is_blacklisted_employee": True,
                "blacklist_reason_id": self.reason_id.id,
                "blacklist_description": self.description,
                "blacklist_date": fields.Datetime.now(),
                "blacklisted_by_id": self.env.user.id,
                "whitelist_date": False,
                "whitelisted_by_id": False,

                # Blacklisted employees are inactive.
                # So they disappear from normal Employees and Interns menus.
                # The view XML will show BLACKLISTED ribbon instead of ARCHIVED.
                "active": False,
            }
        )

        for employee in self.employee_ids:
            employee.message_post(
                body=Markup(
                    "Employee has been blacklisted.<br/>"
                    "<b>Reason:</b> %s<br/>"
                    "<b>Details:</b> %s"
                )
                % (self.reason_id.name, self.description)
            )

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }