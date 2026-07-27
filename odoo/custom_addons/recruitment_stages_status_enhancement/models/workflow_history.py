# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class InternWorkflowHistory(models.Model):
    _name = "intern.workflow.history"
    _description = "Intern Workflow History"
    _order = "action_date desc, id desc"

    name = fields.Char(
        string="Description",
        compute="_compute_name",
        store=True,
    )

    applicant_id = fields.Many2one(
        "intern.applicant",
        string="Intern Applicant",
        required=True,
        ondelete="cascade",
        index=True,
    )

    old_stage_id = fields.Many2one(
        "intern.recruitment.stage",
        string="Previous Stage",
        readonly=True,
    )

    new_stage_id = fields.Many2one(
        "intern.recruitment.stage",
        string="New Stage",
        readonly=True,
    )

    action_type = fields.Selection(
        [
            ("created", "Created"),
            ("approved", "Moved to Next Stage"),
            ("sent_back", "Moved to Previous Stage"),
            ("rejected", "Rejected"),
            ("employee_created", "Employee Created"),
            ("manual_update", "Manual Update"),
        ],
        string="Action",
        required=True,
        default="approved",
        readonly=True,
    )

    action_by_id = fields.Many2one(
        "res.users",
        string="Action By",
        default=lambda self: self.env.user,
        readonly=True,
    )

    action_date = fields.Datetime(
        string="Action Date",
        default=fields.Datetime.now,
        readonly=True,
    )

    remarks = fields.Text(
        string="Remarks",
        readonly=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="applicant_id.company_id",
        store=True,
        readonly=True,
    )

    @api.depends("applicant_id", "old_stage_id", "new_stage_id", "action_type")
    def _compute_name(self):
        for history in self:
            applicant_name = history.applicant_id.partner_name or _("Intern Applicant")
            old_stage = history.old_stage_id.name or _("No Stage")
            new_stage = history.new_stage_id.name or _("No Stage")
            action = dict(history._fields["action_type"].selection).get(
                history.action_type,
                history.action_type,
            )

            history.name = "%s: %s (%s → %s)" % (
                applicant_name,
                action,
                old_stage,
                new_stage,
            )