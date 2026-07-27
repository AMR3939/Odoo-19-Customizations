# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class InternJob(models.Model):
    _name = "intern.job"
    _description = "Intern Job Position"
    _order = "sequence asc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
    )

    name = fields.Char(
        string="Job Position",
        required=True,
        tracking=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        tracking=True,
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        tracking=True,
    )

    recruiter_id = fields.Many2one(
        "res.users",
        string="Recruiter",
        default=lambda self: self.env.user,
        tracking=True,
    )

    interviewer_ids = fields.Many2many(
        comodel_name="res.users",
        relation="intern_job_interviewer_rel",
        column1="intern_job_id",
        column2="user_id",
        string="Interviewers",
        tracking=True,
        domain="[('share', '=', False)]",
        help="Users who can participate in interviewing applicants for this intern job.",
    )

    location = fields.Char(
        string="Location",
        tracking=True,
        default=lambda self: self._get_company_location(self.env.company),
    )

    job_type = fields.Selection(
        [
            ("internship", "Internship"),
            ("trainee", "Trainee"),
            ("apprenticeship", "Apprenticeship"),
        ],
        string="Job Type",
        default="internship",
        required=True,
        tracking=True,
    )

    employment_type = fields.Selection(
        [
            ("internship", "Internship"),
            ("trainee", "Trainee"),
            ("apprenticeship", "Apprenticeship"),
            ("temporary", "Temporary"),
            ("contract", "Contract"),
            ("permanent", "Permanent"),
        ],
        string="Employment Type",
        default="internship",
        required=True,
        tracking=True,
        help="Contract or employment type for this intern job position.",
    )

    expected_skills = fields.Char(
        string="Expected Skills",
        tracking=True,
        help="Expected skills for this intern job. Example: Python: Advanced, JavaScript: Beginner.",
    )
    standard_job_id = fields.Many2one(
        comodel_name="hr.job",
        string="Standard Recruitment Job",
        readonly=True,
        copy=False,
        ondelete="restrict",
        help=(
            "Technical standard Recruitment job record used by Odoo's "
            "Expected Skills selector."
        ),
    )

    current_job_skill_ids = fields.One2many(
        related="standard_job_id.current_job_skill_ids",
        string="Expected Skills",
        readonly=False,
        help="Skills and proficiency levels expected for this intern position.",
    )

    open_positions = fields.Integer(
        string="No of Vacancies",
        default=1,
        tracking=True,
    )

    stipend_min = fields.Float(
        string="Minimum Stipend",
        tracking=True,
    )

    stipend_max = fields.Float(
        string="Maximum Stipend",
        tracking=True,
    )

    description = fields.Html(
        string="Job Description",
    )

    responsibilities = fields.Html(
        string="Responsibilities",
    )

    requirements = fields.Html(
        string="Requirements",
    )

    website_published = fields.Boolean(
        string="Published on Website",
        default=False,
        tracking=True,
    )

    website_url = fields.Char(
        string="Website URL",
        compute="_compute_website_url",
    )

    application_ids = fields.One2many(
        "intern.applicant",
        "job_id",
        string="Intern Applications",
    )

    application_count = fields.Integer(
        string="Total Applications",
        compute="_compute_application_counts",
    )

    open_application_count = fields.Integer(
        string="In Process",
        compute="_compute_application_counts",
    )

    new_application_count = fields.Integer(
        string="New",
        compute="_compute_application_counts",
    )

    hired_count = fields.Integer(
        string="Selected Interns",
        compute="_compute_application_counts",
    )

    post_hiring_count = fields.Integer(
        string="Onboarded Interns",
        compute="_compute_application_counts",
    )

    @api.model
    def _get_company_location(self, company):
        """Return the selected company's address as a single-line location."""
        if not company or not company.partner_id:
            return False

        partner = company.partner_id

        address_parts = [
            partner.street,
            partner.street2,
            partner.city,
            partner.state_id.name if partner.state_id else False,
            partner.zip,
            partner.country_id.name if partner.country_id else False,
        ]

        return ", ".join(
            part.strip()
            for part in address_parts
            if part and part.strip()
        )

    @api.onchange("company_id")
    def _onchange_company_id_set_location(self):
        """Automatically fill Location when Company is selected or changed."""
        for job in self:
            job.location = (
                job._get_company_location(job.company_id)
                if job.company_id
                else False
            )

    @api.depends("website_published")
    def _compute_website_url(self):
        for job in self:
            if job.id:
                job.website_url = "/intern/jobs/%s" % job.id
            else:
                job.website_url = False

    @api.depends(
        "application_ids",
        "application_ids.active",
        "application_ids.stage_id",
        "application_ids.stage_id.intern_workflow_category",
        "application_ids.stage_id.intern_rejected_stage",
    )
    def _compute_application_counts(self):
        """
        Dashboard count logic:

        New:
            Applicants currently in Applicant stage.

        In Process:
            Applicants currently in Screening / First Interview / Second Interview.

        Selected Interns:
            Applicants currently in Selected stage only.

        Onboarded Interns:
            Applicants currently in Onboarding / Active / Relieving Process / Completed.

        No of Vacancies:
            open_positions field.
        """

        for job in self:
            active_applications = job.application_ids.filtered(
                lambda applicant: applicant.active
            )

            job.application_count = len(active_applications)

            job.new_application_count = len(
                active_applications.filtered(
                    lambda applicant:
                    applicant.stage_id
                    and applicant.stage_id.intern_workflow_category == "application"
                    and not applicant.stage_id.intern_rejected_stage
                )
            )

            job.open_application_count = len(
                active_applications.filtered(
                    lambda applicant:
                    applicant.stage_id
                    and applicant.stage_id.intern_workflow_category in [
                        "screening",
                        "interview",
                    ]
                    and not applicant.stage_id.intern_rejected_stage
                )
            )

            job.hired_count = len(
                active_applications.filtered(
                    lambda applicant:
                    applicant.stage_id
                    and applicant.stage_id.intern_workflow_category == "selection"
                    and not applicant.stage_id.intern_rejected_stage
                )
            )

            job.post_hiring_count = len(
                active_applications.filtered(
                    lambda applicant:
                    applicant.stage_id
                    and applicant.stage_id.intern_workflow_category in [
                        "onboarding",
                        "active",
                        "exit",
                        "completed",
                    ]
                    and not applicant.stage_id.intern_rejected_stage
                )
            )

    @api.constrains("open_positions")
    def _check_open_positions(self):
        for job in self:
            if job.open_positions < 0:
                raise ValidationError(_("No of vacancies cannot be negative."))

    @api.constrains("stipend_min", "stipend_max")
    def _check_stipend_range(self):
        for job in self:
            if job.stipend_min < 0 or job.stipend_max < 0:
                raise ValidationError(_("Stipend amount cannot be negative."))

            if job.stipend_min and job.stipend_max and job.stipend_min > job.stipend_max:
                raise ValidationError(
                    _("Minimum stipend cannot be greater than maximum stipend.")
                )

    def _get_standard_job_bridge_vals(self):
        """
        Prepare values for the hidden standard hr.job record.

        The hidden hr.job is used only to connect this intern job to
        Odoo's standard Expected Skills functionality.
        """
        self.ensure_one()

        hr_job_fields = self.env["hr.job"]._fields

        values = {
            "name": self.name,
            "company_id": self.company_id.id,
            "active": False,
        }

        if "department_id" in hr_job_fields:
            values["department_id"] = (
                self.department_id.id
                if self.department_id
                else False
            )

        if "user_id" in hr_job_fields:
            values["user_id"] = (
                self.recruiter_id.id
                if self.recruiter_id
                else False
            )

        if "interviewer_ids" in hr_job_fields:
            values["interviewer_ids"] = [
                (6, 0, self.interviewer_ids.ids)
            ]

        if "address_id" in hr_job_fields:
            values["address_id"] = (
                self.company_id.partner_id.id
                if self.company_id and self.company_id.partner_id
                else False
            )

        return values

    @api.model_create_multi
    def create(self, vals_list):
        """
        Create a hidden standard hr.job record for every new intern job.
        """
        records = super().create(vals_list)

        for record in records:
            if record.standard_job_id:
                continue

            standard_job = self.env["hr.job"].with_context(
                active_test=False
            ).create(
                record._get_standard_job_bridge_vals()
            )

            record.with_context(
                skip_standard_job_bridge_sync=True
            ).write(
                {
                    "standard_job_id": standard_job.id,
                }
            )

        return records

    def write(self, vals):
        """
        Synchronize relevant intern-job details with the hidden hr.job.
        """
        result = super().write(vals)

        if self.env.context.get("skip_standard_job_bridge_sync"):
            return result

        synchronized_fields = {
            "name",
            "company_id",
            "department_id",
            "recruiter_id",
            "interviewer_ids",
        }

        if synchronized_fields.intersection(vals):
            for record in self.filtered("standard_job_id"):
                record.standard_job_id.with_context(
                    active_test=False
                ).write(
                    record._get_standard_job_bridge_vals()
                )

        return result

    def unlink(self):
        """
        Delete the hidden standard hr.job when the intern job is deleted.
        """
        standard_jobs = self.mapped("standard_job_id")

        result = super().unlink()

        if standard_jobs:
            standard_jobs.with_context(
                active_test=False
            ).unlink()

        return result

    def _get_initial_intern_stage(self):
        return self.env["intern.recruitment.stage"].get_default_intern_stage()

    def _get_intern_context(self):
        self.ensure_one()

        context = {
            "default_job_id": self.id,
            "default_company_id": self.company_id.id,
            "default_recruiter_id": self.recruiter_id.id,
            "intern_recruitment_mode": True,
            "search_default_job_id": self.id,
            "search_default_group_stage": 1,
        }

        initial_stage = self._get_initial_intern_stage()
        if initial_stage:
            context["default_stage_id"] = initial_stage.id

        return context

    def _get_intern_applicant_views(self):
        return [
            (
                self.env.ref(
                    "recruitment_stages_status_enhancement.view_intern_applicant_kanban"
                ).id,
                "kanban",
            ),
            (
                self.env.ref(
                    "recruitment_stages_status_enhancement.view_intern_applicant_list"
                ).id,
                "list",
            ),
            (
                self.env.ref(
                    "recruitment_stages_status_enhancement.view_intern_applicant_form"
                ).id,
                "form",
            ),
            (False, "activity"),
        ]
    
    def action_open_activities(self):
        """
        Open activities for every intern applicant belonging
        to the selected intern job position.
        """
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Intern Applicant Activities"),
            "res_model": "intern.applicant",
            "view_mode": "activity,kanban,list,form",
            "views": [
                (False, "activity"),
                (
                    self.env.ref(
                        "recruitment_stages_status_enhancement."
                        "view_intern_applicant_kanban"
                    ).id,
                    "kanban",
                ),
                (
                    self.env.ref(
                        "recruitment_stages_status_enhancement."
                        "view_intern_applicant_list"
                    ).id,
                    "list",
                ),
                (
                    self.env.ref(
                        "recruitment_stages_status_enhancement."
                        "view_intern_applicant_form"
                    ).id,
                    "form",
                ),
            ],
            "search_view_id": self.env.ref(
                "recruitment_stages_status_enhancement."
                "view_intern_applicant_activity_search"
            ).id,
            "domain": [
                ("job_id", "=", self.id),
            ],
            "context": {
                "active_test": False,
                "default_job_id": self.id,
                "default_company_id": self.company_id.id,
                "default_recruiter_id": self.recruiter_id.id,
                "search_default_job_id": self.id,
                "intern_recruitment_mode": True,
            },
            "target": "current",
        }

    def action_open_applications(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Intern Applications"),
            "res_model": "intern.applicant",
            "view_mode": "kanban,list,form,activity",
            "views": self._get_intern_applicant_views(),
            "search_view_id": self.env.ref(
                "recruitment_stages_status_enhancement.view_intern_applicant_search"
            ).id,
            "domain": [
                ("job_id", "=", self.id),
            ],
            "context": self._get_intern_context(),
            "target": "current",
        }

    def action_create_application(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("New Intern Application"),
            "res_model": "intern.applicant",
            "view_mode": "form",
            "views": [
                (
                    self.env.ref(
                        "recruitment_stages_status_enhancement.view_intern_applicant_form"
                    ).id,
                    "form",
                )
            ],
            "context": self._get_intern_context(),
            "target": "current",
        }

    def action_open_post_hiring_interns(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Onboarded Interns"),
            "res_model": "intern.applicant",
            "view_mode": "kanban,list,form,activity",
            "views": self._get_intern_applicant_views(),
            "search_view_id": self.env.ref(
                "recruitment_stages_status_enhancement.view_intern_applicant_search"
            ).id,
            "domain": [
                ("job_id", "=", self.id),
                (
                    "stage_id.intern_workflow_category",
                    "in",
                    ["onboarding", "active", "exit", "completed"],
                ),
            ],
            "context": self._get_intern_context(),
            "target": "current",
        }

    def action_publish_job(self):
        for job in self:
            job.website_published = True
        return True

    def action_unpublish_job(self):
        for job in self:
            job.website_published = False
        return True

    def action_open_website_page(self):
        self.ensure_one()

        if not self.website_published:
            raise UserError(
                _("Please publish this intern job before opening the website page.")
            )

        if not self.website_url:
            raise UserError(_("Website URL is not available."))

        return {
            "type": "ir.actions.act_url",
            "url": self.website_url,
            "target": "new",
        }