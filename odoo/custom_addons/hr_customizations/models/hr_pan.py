# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


PAN_PATTERN = r"^[A-Z]{5}[0-9]{4}[A-Z]$"


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    pan_number = fields.Char(
        string="PAN Number",
        tracking=True,
        copy=False,
        help="Permanent Account Number used for blacklist verification.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("pan_number"):
                vals["pan_number"] = vals["pan_number"].strip().upper()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("pan_number"):
            vals["pan_number"] = vals["pan_number"].strip().upper()
        return super().write(vals)

    @api.onchange("pan_number")
    def _onchange_pan_number(self):
        for employee in self:
            if employee.pan_number:
                employee.pan_number = employee.pan_number.strip().upper()

    @api.constrains("pan_number")
    def _check_pan_number(self):
        for employee in self:
            if not employee.pan_number:
                continue

            pan = employee.pan_number.strip().upper()

            if not re.match(PAN_PATTERN, pan):
                raise ValidationError(
                    _(
                        "Please enter a valid PAN number. "
                        "Example format: ABCDE1234F"
                    )
                )


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    pan_number = fields.Char(
        string="PAN Number",
        tracking=True,
        copy=False,
        help="Permanent Account Number used for blacklist verification.",
    )

    # ---------------------------------------------------------
    # PAN Helpers
    # ---------------------------------------------------------

    def _normalize_pan_number(self, pan_number):
        return (pan_number or "").strip().upper()

    def _validate_pan_format(self, pan_number):
        if pan_number and not re.match(PAN_PATTERN, pan_number):
            raise ValidationError(
                _(
                    "Please enter a valid PAN number. "
                    "Example format: ABCDE1234F"
                )
            )

    def _get_blacklisted_employee_by_pan(self, pan_number):
        if not pan_number:
            return self.env["hr.employee"]

        return (
            self.env["hr.employee"]
            .sudo()
            .with_context(active_test=False)
            .search(
                [
                    ("pan_number", "=", pan_number),
                    ("is_blacklisted_employee", "=", True),
                ],
                limit=1,
            )
        )

    def _raise_blacklisted_pan_error(self, blacklisted_employee):
        reason = (
            blacklisted_employee.blacklist_reason_id.name
            if blacklisted_employee.blacklist_reason_id
            else _("No reason specified")
        )

        details = blacklisted_employee.blacklist_description or _("No detailed reason provided")

        raise ValidationError(
            _(
                "This applicant is already blacklisted.\n\n"
                "Blacklisted Employee: %s\n"
                "PAN Number: %s\n"
                "Reason: %s\n"
                "Details: %s"
            )
            % (
                blacklisted_employee.name,
                blacklisted_employee.pan_number,
                reason,
                details,
            )
        )

    def _check_blacklisted_pan_number(self, pan_number):
        pan_number = self._normalize_pan_number(pan_number)

        if not pan_number:
            return

        blacklisted_employee = self._get_blacklisted_employee_by_pan(pan_number)

        if blacklisted_employee:
            self._raise_blacklisted_pan_error(blacklisted_employee)

    # ---------------------------------------------------------
    # Create / Write
    # ---------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("pan_number"):
                vals["pan_number"] = self._normalize_pan_number(vals["pan_number"])
                self._validate_pan_format(vals["pan_number"])
                self._check_blacklisted_pan_number(vals["pan_number"])

        return super().create(vals_list)

    def write(self, vals):
        if vals.get("pan_number"):
            vals["pan_number"] = self._normalize_pan_number(vals["pan_number"])
            self._validate_pan_format(vals["pan_number"])
            self._check_blacklisted_pan_number(vals["pan_number"])

        return super().write(vals)

    # ---------------------------------------------------------
    # Onchange / Constraints
    # ---------------------------------------------------------

    @api.onchange("pan_number")
    def _onchange_pan_number(self):
        for applicant in self:
            if applicant.pan_number:
                applicant.pan_number = applicant.pan_number.strip().upper()

    @api.constrains("pan_number")
    def _check_pan_number(self):
        for applicant in self:
            if not applicant.pan_number:
                continue

            pan = applicant.pan_number.strip().upper()
            applicant._validate_pan_format(pan)
            applicant._check_blacklisted_pan_number(pan)