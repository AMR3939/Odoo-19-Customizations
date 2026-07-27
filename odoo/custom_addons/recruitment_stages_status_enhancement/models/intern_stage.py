# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InternRecruitmentStage(models.Model):
    _name = "intern.recruitment.stage"
    _description = "Intern Recruitment Stage"
    _order = "sequence asc, id asc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Stage Name",
        required=True,
        tracking=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        tracking=True,
        help="Controls the order of stages in the intern workflow.",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

    fold = fields.Boolean(
        string="Folded in Kanban",
        default=False,
        help="Fold this stage in Kanban view.",
    )

    color = fields.Integer(
        string="Color",
        default=0,
    )

    intern_workflow_category = fields.Selection(
        [
            ("application", "Application"),
            ("screening", "Screening"),
            ("interview", "Interview"),
            ("selection", "Selection"),
            ("onboarding", "Onboarding"),
            ("active", "Active"),
            ("exit", "Exit"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
        ],
        string="Stage Category",
        default="application",
        required=True,
        tracking=True,
    )

    intern_requires_approval = fields.Boolean(
        string="Requires Approval",
        default=True,
        tracking=True,
        help="If enabled, applicants can move through this stage only using workflow buttons.",
    )

    intern_allow_send_back = fields.Boolean(
        string="Allow Move to Previous Stage",
        default=True,
        tracking=True,
    )

    intern_allow_reject = fields.Boolean(
        string="Allow Reject",
        default=True,
        tracking=True,
    )

    intern_initial_stage = fields.Boolean(
        string="Initial Stage",
        default=False,
        tracking=True,
        help="Only one stage should be marked as the initial stage.",
    )

    intern_final_stage = fields.Boolean(
        string="Final Stage",
        default=False,
        tracking=True,
        help="Normal next-stage movement stops at this stage.",
    )

    intern_rejected_stage = fields.Boolean(
        string="Rejected Stage",
        default=False,
        tracking=True,
        help="Rejected stage is used only through the Reject action.",
    )

    intern_create_employee_stage = fields.Boolean(
        string="Create Employee Stage",
        default=False,
        tracking=True,
        help="Employee creation is allowed only at this stage.",
    )

    intern_is_post_hiring_stage = fields.Boolean(
        string="Post-Hiring Stage",
        default=False,
        tracking=True,
        help="Enable this for stages after selection/hiring.",
    )

    description = fields.Text(
        string="Description",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        This model is already dedicated to Intern Recruitment.

        So every stage created here automatically belongs to our intern workflow.
        No relation with Odoo's default hr.recruitment.stage is used.
        """
        for vals in vals_list:
            vals.setdefault("intern_requires_approval", True)
            vals.setdefault("intern_allow_send_back", True)
            vals.setdefault("intern_allow_reject", True)
            vals.setdefault("fold", False)

            if vals.get("intern_rejected_stage"):
                vals["intern_workflow_category"] = "rejected"

            if vals.get("intern_final_stage"):
                vals.setdefault("intern_workflow_category", "completed")

        return super().create(vals_list)

    def write(self, vals):
        """
        Keep category consistent for rejected/final stages.
        """
        if vals.get("intern_rejected_stage"):
            vals["intern_workflow_category"] = "rejected"

        if vals.get("intern_final_stage") and not vals.get("intern_workflow_category"):
            vals["intern_workflow_category"] = "completed"

        return super().write(vals)

    @api.constrains("intern_initial_stage", "active")
    def _check_single_initial_stage(self):
        for stage in self:
            if stage.active and stage.intern_initial_stage:
                existing = self.search_count(
                    [
                        ("active", "=", True),
                        ("intern_initial_stage", "=", True),
                        ("id", "!=", stage.id),
                    ]
                )
                if existing:
                    raise ValidationError(
                        "Only one active intern workflow stage can be marked as initial."
                    )

    @api.constrains("intern_rejected_stage", "active")
    def _check_single_rejected_stage(self):
        for stage in self:
            if stage.active and stage.intern_rejected_stage:
                existing = self.search_count(
                    [
                        ("active", "=", True),
                        ("intern_rejected_stage", "=", True),
                        ("id", "!=", stage.id),
                    ]
                )
                if existing:
                    raise ValidationError(
                        "Only one active intern workflow stage can be marked as rejected."
                    )

    @api.constrains("intern_final_stage", "intern_rejected_stage")
    def _check_rejected_not_final(self):
        for stage in self:
            if stage.intern_final_stage and stage.intern_rejected_stage:
                raise ValidationError(
                    "Rejected stage cannot also be the final workflow stage."
                )

    @api.model
    def _get_ordered_intern_workflow_stages(self):
        """
        Returns all normal intern workflow stages in sequence order.

        Rejected stage is excluded because rejection is a separate action,
        not part of normal next/previous movement.
        """
        return self.search(
            [
                ("active", "=", True),
                ("intern_rejected_stage", "=", False),
            ],
            order="sequence asc, id asc",
        )

    @api.model
    def get_default_intern_stage(self):
        """
        Returns the initial stage.

        Priority:
        1. Stage explicitly marked as Initial Stage
        2. First active non-rejected stage by sequence

        This supports dynamic stages. If a new stage is added before Applicant
        with a lower sequence and marked initial, it can become the first stage.
        """
        initial_stage = self.search(
            [
                ("active", "=", True),
                ("intern_initial_stage", "=", True),
                ("intern_rejected_stage", "=", False),
            ],
            order="sequence asc, id asc",
            limit=1,
        )

        if initial_stage:
            return initial_stage

        return self.search(
            [
                ("active", "=", True),
                ("intern_rejected_stage", "=", False),
                ("intern_final_stage", "=", False),
            ],
            order="sequence asc, id asc",
            limit=1,
        )

    @api.model
    def get_rejected_intern_stage(self):
        """
        Returns the rejected stage.
        """
        return self.search(
            [
                ("active", "=", True),
                ("intern_rejected_stage", "=", True),
            ],
            order="sequence asc, id asc",
            limit=1,
        )

    def get_next_intern_stage(self):
        """
        Returns the immediate next intern stage based on sequence.

        Example:
            Applicant      sequence 10
            Test Stage     sequence 15
            Screening      sequence 20

        If current stage is Applicant, next stage becomes Test Stage.
        """
        self.ensure_one()

        if self.intern_rejected_stage or self.intern_final_stage:
            return False

        ordered_stages = self._get_ordered_intern_workflow_stages()
        stage_ids = ordered_stages.ids

        if self.id not in stage_ids:
            return False

        current_index = stage_ids.index(self.id)
        next_index = current_index + 1

        if next_index >= len(ordered_stages):
            return False

        return ordered_stages[next_index]

    def get_previous_intern_stage(self):
        """
        Returns the immediate previous intern stage based on sequence.
        """
        self.ensure_one()

        if self.intern_rejected_stage:
            return False

        ordered_stages = self._get_ordered_intern_workflow_stages()
        stage_ids = ordered_stages.ids

        if self.id not in stage_ids:
            return False

        current_index = stage_ids.index(self.id)

        if current_index <= 0:
            return False

        return ordered_stages[current_index - 1]