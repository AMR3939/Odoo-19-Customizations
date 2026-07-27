# -*- coding: utf-8 -*-

from odoo import fields, models, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    intern_applicant_id = fields.Many2one(
        "hr.applicant",
        string="Intern Applicant",
        readonly=True,
        copy=False,
        help="Intern recruitment record from which this employee was created.",
    )

    def action_open_intern_applicant(self):
        self.ensure_one()

        if not self.intern_applicant_id:
            return False

        return {
            "type": "ir.actions.act_window",
            "name": _("Intern Applicant"),
            "res_model": "hr.applicant",
            "view_mode": "form",
            "res_id": self.intern_applicant_id.id,
            "target": "current",
            "context": {"intern_recruitment_mode": True},
        }
