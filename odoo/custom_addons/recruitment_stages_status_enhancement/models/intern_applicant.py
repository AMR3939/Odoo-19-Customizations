# -*- coding: utf-8 -*-

import mimetypes
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


PAN_PATTERN = r"^[A-Z]{5}[0-9]{4}[A-Z]$"


class InternApplicant(models.Model):
    _name = "intern.applicant"
    _description = "Intern Applicant"
    _order = "priority desc, sequence asc, id desc"
    _rec_name = "partner_name"
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

    color = fields.Integer(
        string="Color",
        default=0,
    )

    priority = fields.Selection(
        [
            ("0", "Normal"),
            ("1", "Good"),
            ("2", "Very Good"),
            ("3", "Excellent"),
        ],
        string="Evaluation",
        default="0",
        tracking=True,
    )

    application_status = fields.Selection(
        [
            ("ongoing", "Ongoing"),
            ("rejected", "Rejected"),
            ("hired", "Hired"),
            ("completed", "Completed"),
            ("archived", "Archived"),
        ],
        string="Application Status",
        default="ongoing",
        tracking=True,
    )

    intern_reference = fields.Char(
        string="Intern Reference",
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
    )

    intern_first_name = fields.Char(
        string="First Name",
        required=True,
        tracking=True,
    )

    intern_middle_name = fields.Char(
        string="Middle Name",
        tracking=True,
    )

    intern_last_name = fields.Char(
        string="Last Name",
        required=True,
        tracking=True,
    )

    partner_name = fields.Char(
        string="Applicant Name",
        compute="_compute_partner_name",
        store=True,
        readonly=False,
        tracking=True,
    )

    email_from = fields.Char(
        string="Email",
        required=True,
        tracking=True,
    )

    partner_phone = fields.Char(
        string="Mobile Number",
        required=True,
        tracking=True,
    )

    pan_number = fields.Char(
        string="PAN Number",
        required=True,
        tracking=True,
        copy=False,
        help="Permanent Account Number used for blacklist verification.",
    )

    linkedin_profile = fields.Char(
        string="LinkedIn Profile",
        tracking=True,
    )

    type_id = fields.Char(
        string="Degree / Qualification",
        tracking=True,
        help="Legacy text qualification field. Use Degree, Stream, and University fields for structured education details.",
    )

    degree_id = fields.Many2one(
        "hr.employee.degree",
        string="Degree",
        tracking=True,
        ondelete="restrict",
    )

    stream_id = fields.Many2one(
        "hr.employee.stream",
        string="Stream",
        tracking=True,
        ondelete="restrict",
    )

    university_id = fields.Many2one(
        "hr.employee.university",
        string="University",
        tracking=True,
        ondelete="restrict",
    )

    university_city_id = fields.Many2one(
        "res.city",
        string="University City",
        compute="_compute_university_location",
        store=True,
        readonly=True,
    )

    university_state_id = fields.Many2one(
        "res.country.state",
        string="University State",
        compute="_compute_university_location",
        store=True,
        readonly=True,
    )

    university_country_id = fields.Many2one(
        "res.country",
        string="University Country",
        compute="_compute_university_location",
        store=True,
        readonly=True,
    )

    availability = fields.Date(
        string="Availability / Joining Date",
        required=True,
        tracking=True,
    )

    salary_expected = fields.Float(
        string="Expected Stipend",
        tracking=True,
    )

    salary_expected_extra = fields.Char(
        string="Expected Stipend Extra",
        tracking=True,
    )

    salary_proposed = fields.Float(
        string="Proposed Stipend",
        tracking=True,
    )

    salary_proposed_extra = fields.Char(
        string="Proposed Stipend Extra",
        tracking=True,
    )

    applicant_notes = fields.Html(
        string="Notes",
    )

    resume_file = fields.Binary(
        string="Resume",
        attachment=True,
        copy=False,
    )

    resume_filename = fields.Char(
        string="Resume Filename",
        copy=False,
    )

    message_main_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Main Attachment",
        copy=False,
        readonly=True,
        ondelete="set null",
    )

    job_id = fields.Many2one(
        "intern.job",
        string="Intern Job Position",
        required=True,
        tracking=True,
        ondelete="restrict",
    )

    stage_id = fields.Many2one(
        "intern.recruitment.stage",
        string="Stage",
        required=True,
        tracking=True,
        ondelete="restrict",
        group_expand="_read_group_stage_ids",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="job_id.company_id",
        store=True,
        readonly=True,
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        related="job_id.department_id",
        store=True,
        readonly=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Recruiter",
        related="job_id.recruiter_id",
        store=True,
        readonly=True,
    )

    interviewer_ids = fields.Many2many(
        "res.users",
        "intern_applicant_interviewer_rel",
        "applicant_id",
        "user_id",
        string="Interviewers",
    )

    categ_ids = fields.Many2many(
        "hr.applicant.category",
        "intern_applicant_category_rel",
        "applicant_id",
        "category_id",
        string="Tags",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        copy=False,
        readonly=True,
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        copy=False,
        readonly=True,
    )

    date_closed = fields.Datetime(
        string="Closed / Hired Date",
        readonly=True,
        copy=False,
    )

    intern_workflow_history_ids = fields.One2many(
        "intern.workflow.history",
        "applicant_id",
        string="Workflow History",
        readonly=True,
    )

    intern_stage_category = fields.Selection(
        related="stage_id.intern_workflow_category",
        string="Intern Stage Category",
        store=True,
        readonly=True,
    )

    intern_is_post_hiring = fields.Boolean(
        related="stage_id.intern_is_post_hiring_stage",
        string="Post-Hiring Stage",
        store=True,
        readonly=True,
    )

    intern_can_approve = fields.Boolean(
        string="Can Move to Next Stage",
        compute="_compute_intern_workflow_buttons",
    )

    intern_can_send_back = fields.Boolean(
        string="Can Move to Previous Stage",
        compute="_compute_intern_workflow_buttons",
    )

    intern_can_reject = fields.Boolean(
        string="Can Reject",
        compute="_compute_intern_workflow_buttons",
    )

    intern_can_create_employee = fields.Boolean(
        string="Can Create Employee",
        compute="_compute_intern_workflow_buttons",
    )

    # ---------------------------------------------------------
    # Name Handling
    # ---------------------------------------------------------

    @api.depends("intern_first_name", "intern_middle_name", "intern_last_name")
    def _compute_partner_name(self):
        for applicant in self:
            applicant.partner_name = applicant._get_intern_full_name()

    def _get_intern_full_name(self):
        self.ensure_one()

        return " ".join(
            part.strip()
            for part in [
                self.intern_first_name,
                self.intern_middle_name,
                self.intern_last_name,
            ]
            if part and part.strip()
        )

    @api.onchange("intern_first_name", "intern_middle_name", "intern_last_name")
    def _onchange_intern_name_parts(self):
        for applicant in self:
            applicant.partner_name = applicant._get_intern_full_name()

    @api.onchange("pan_number")
    def _onchange_pan_number(self):
        for applicant in self:
            if applicant.pan_number:
                applicant.pan_number = applicant.pan_number.strip().upper()

    @api.onchange("degree_id")
    def _onchange_degree_id(self):
        for applicant in self:
            if applicant.degree_id:
                applicant.type_id = applicant.degree_id.name
            else:
                applicant.type_id = False
    @api.depends(
        "university_id",
        "university_id.city_id",
        "university_id.city_id.state_id",
        "university_id.city_id.country_id",
        "university_id.city_id.state_id.country_id",
    )
    def _compute_university_location(self):
        for applicant in self:
            city = applicant.university_id.city_id if applicant.university_id else False
            state = city.state_id if city else False
            country = False

            if city:
                country = city.country_id or (
                    state.country_id if state else False
                )

            applicant.university_city_id = city
            applicant.university_state_id = state
            applicant.university_country_id = country

    # ---------------------------------------------------------
    # PAN / Blacklist Helpers
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

        Employee = self.env["hr.employee"].sudo().with_context(active_test=False)

        if (
            "pan_number" not in Employee._fields
            or "is_blacklisted_employee" not in Employee._fields
        ):
            return Employee.browse()

        return Employee.search(
            [
                ("pan_number", "=", pan_number),
                ("is_blacklisted_employee", "=", True),
            ],
            limit=1,
        )

    def _raise_blacklisted_pan_error(self, blacklisted_employee):
        reason = _("No reason specified")
        details = _("No detailed reason provided")

        if (
            "blacklist_reason_id" in blacklisted_employee._fields
            and blacklisted_employee.blacklist_reason_id
        ):
            reason = blacklisted_employee.blacklist_reason_id.name

        if (
            "blacklist_description" in blacklisted_employee._fields
            and blacklisted_employee.blacklist_description
        ):
            details = blacklisted_employee.blacklist_description

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
    # Resume Attachment Preview
    # ---------------------------------------------------------

    def _sync_resume_main_attachment(self):
        Attachment = self.env["ir.attachment"].sudo()

        for applicant in self:
            if not applicant.resume_file:
                continue

            if "message_main_attachment_id" not in applicant._fields:
                continue

            filename = applicant.resume_filename or _("Resume")
            mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

            attachment = False

            if applicant.message_main_attachment_id:
                attachment = applicant.message_main_attachment_id.sudo()

            if not attachment:
                attachment = Attachment.search(
                    [
                        ("res_model", "=", applicant._name),
                        ("res_id", "=", applicant.id),
                        ("name", "=", filename),
                    ],
                    limit=1,
                )

            attachment_vals = {
                "name": filename,
                "datas": applicant.resume_file,
                "res_model": applicant._name,
                "res_id": applicant.id,
                "type": "binary",
                "mimetype": mimetype,
            }

            if attachment:
                attachment.write(attachment_vals)
            else:
                attachment = Attachment.create(attachment_vals)

            applicant.with_context(
                skip_resume_attachment_sync=True,
                allow_intern_stage_change=True,
            ).sudo().write(
                {
                    "message_main_attachment_id": attachment.id,
                }
            )

    # ---------------------------------------------------------
    # Default Values
    # ---------------------------------------------------------

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)

        if "stage_id" in fields_list and not values.get("stage_id"):
            default_stage = self.env["intern.recruitment.stage"].get_default_intern_stage()
            if default_stage:
                values["stage_id"] = default_stage.id

        return values

    # ---------------------------------------------------------
    # Create / Write
    # ---------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        sequence_obj = self.env["ir.sequence"]
        stage_obj = self.env["intern.recruitment.stage"]

        for vals in vals_list:
            if vals.get("pan_number"):
                vals["pan_number"] = self._normalize_pan_number(vals["pan_number"])
                self._validate_pan_format(vals["pan_number"])
                self._check_blacklisted_pan_number(vals["pan_number"])

            if vals.get("degree_id") and not vals.get("type_id"):
                degree = self.env["hr.employee.degree"].sudo().browse(vals["degree_id"])
                vals["type_id"] = degree.name if degree.exists() else False

            if vals.get("intern_reference", "New") == "New":
                vals["intern_reference"] = (
                    sequence_obj.next_by_code("intern.applicant.sequence") or "New"
                )

            if not vals.get("stage_id"):
                default_stage = stage_obj.get_default_intern_stage()
                if default_stage:
                    vals["stage_id"] = default_stage.id

        applicants = super().create(vals_list)

        applicants._sync_resume_main_attachment()

        for applicant in applicants:
            applicant._validate_intern_required_fields()
            applicant._create_or_update_intern_contact()
            applicant._create_intern_workflow_history(
                old_stage=False,
                new_stage=applicant.stage_id,
                action_type="created",
                remarks=_("Intern applicant created."),
            )

        return applicants

    def write(self, vals):
        if vals.get("pan_number"):
            vals["pan_number"] = self._normalize_pan_number(vals["pan_number"])
            self._validate_pan_format(vals["pan_number"])
            self._check_blacklisted_pan_number(vals["pan_number"])

        if vals.get("degree_id") and not vals.get("type_id"):
            degree = self.env["hr.employee.degree"].sudo().browse(vals["degree_id"])
            vals["type_id"] = degree.name if degree.exists() else False

        if "stage_id" in vals and not self.env.context.get("allow_intern_stage_change"):
            for applicant in self:
                if applicant.stage_id and applicant.stage_id.id != vals.get("stage_id"):
                    raise UserError(
                        _(
                            "You cannot move an intern applicant by dragging or directly changing the stage. "
                            "Please use Move to Next Stage, Move to Previous Stage, or Reject."
                        )
                    )

        result = super().write(vals)

        if (
            not self.env.context.get("skip_resume_attachment_sync")
            and ("resume_file" in vals or "resume_filename" in vals)
        ):
            self._sync_resume_main_attachment()

        for applicant in self:
            applicant._validate_intern_required_fields()

        return result

    # ---------------------------------------------------------
    # Kanban Stage Expansion
    # ---------------------------------------------------------

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return self.env["intern.recruitment.stage"].search(
            [("active", "=", True)],
            order="sequence asc, id asc",
        )

    # ---------------------------------------------------------
    # Button Visibility
    # ---------------------------------------------------------

    @api.depends(
        "stage_id",
        "stage_id.intern_final_stage",
        "stage_id.intern_rejected_stage",
        "stage_id.intern_allow_send_back",
        "stage_id.intern_allow_reject",
        "stage_id.intern_create_employee_stage",
        "employee_id",
        "active",
        "application_status",
    )
    def _compute_intern_workflow_buttons(self):
        for applicant in self:
            applicant.intern_can_approve = False
            applicant.intern_can_send_back = False
            applicant.intern_can_reject = False
            applicant.intern_can_create_employee = False

            if not applicant.active or not applicant.stage_id:
                continue

            stage = applicant.stage_id

            if stage.intern_rejected_stage:
                continue

            if not stage.intern_final_stage:
                applicant.intern_can_approve = bool(stage.get_next_intern_stage())

            if stage.intern_allow_send_back:
                applicant.intern_can_send_back = bool(stage.get_previous_intern_stage())

            if stage.intern_allow_reject:
                applicant.intern_can_reject = bool(
                    self.env["intern.recruitment.stage"].get_rejected_intern_stage()
                )

            if stage.intern_create_employee_stage and not applicant.employee_id:
                applicant.intern_can_create_employee = True

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    @api.constrains(
        "intern_first_name",
        "intern_middle_name",
        "intern_last_name",
        "email_from",
        "partner_phone",
        "pan_number",
        "job_id",
        "type_id",
        "degree_id",
        "stream_id",
        "university_id",
        "availability",
        "linkedin_profile",
        "salary_expected",
        "salary_proposed",
        "active",
    )
    def _check_intern_application_validation(self):
        self._validate_intern_required_fields()

    def _validate_intern_required_fields(self):
        today = fields.Date.context_today(self)

        for applicant in self:
            if not applicant.active:
                continue

            missing = []

            first_name = (applicant.intern_first_name or "").strip()
            middle_name = (applicant.intern_middle_name or "").strip()
            last_name = (applicant.intern_last_name or "").strip()
            email = (applicant.email_from or "").strip()
            phone = (applicant.partner_phone or "").strip()
            pan = applicant._normalize_pan_number(applicant.pan_number)
            linkedin = (applicant.linkedin_profile or "").strip()

            if not first_name:
                missing.append(_("First Name"))
            if not last_name:
                missing.append(_("Last Name"))
            if not email:
                missing.append(_("Email"))
            if not phone:
                missing.append(_("Mobile Number"))
            if not pan:
                missing.append(_("PAN Number"))
            if not applicant.job_id:
                missing.append(_("Intern Job Position"))
            if not applicant.degree_id and not applicant.type_id:
                missing.append(_("Degree"))
            if not applicant.university_id:
                missing.append(_("University"))
            if not applicant.availability:
                missing.append(_("Availability / Joining Date"))

            if missing:
                raise ValidationError(
                    _("Please fill the required intern application fields: %s")
                    % ", ".join(missing)
                )

            name_pattern = r"^[A-Za-z][A-Za-z\s.'-]*$"

            for label, value, required in [
                (_("First Name"), first_name, True),
                (_("Middle Name"), middle_name, False),
                (_("Last Name"), last_name, True),
            ]:
                if not value and not required:
                    continue

                if len(value) < 2 or len(value) > 50:
                    raise ValidationError(
                        _("%s must be between 2 and 50 characters.") % label
                    )

                if not re.match(name_pattern, value):
                    raise ValidationError(
                        _(
                            "%s can contain only letters, spaces, dot, apostrophe, and hyphen."
                        )
                        % label
                    )

            if len(email) > 128 or not tools.email_normalize(email):
                raise ValidationError(_("Please enter a valid email address."))

            phone_digits = re.sub(r"\D", "", phone)

            if len(phone_digits) != 10:
                raise ValidationError(_("Mobile number must contain exactly 10 digits."))

            if not re.match(r"^[6-9]\d{9}$", phone_digits):
                raise ValidationError(
                    _(
                        "Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9."
                    )
                )

            self._validate_pan_format(pan)
            self._check_blacklisted_pan_number(pan)

            if applicant.availability and applicant.availability < today:
                raise ValidationError(
                    _("Availability / Joining Date cannot be in the past.")
                )

            if linkedin:
                linkedin_pattern = r"^https://(www\.)?linkedin\.com/in/[A-Za-z0-9_\-%]+/?$"
                if not re.match(linkedin_pattern, linkedin):
                    raise ValidationError(
                        _(
                            "Please enter a valid LinkedIn profile URL. "
                            "Example: https://www.linkedin.com/in/username"
                        )
                    )

            if applicant.salary_expected and applicant.salary_expected < 0:
                raise ValidationError(_("Expected stipend cannot be negative."))

            if applicant.salary_proposed and applicant.salary_proposed < 0:
                raise ValidationError(_("Proposed stipend cannot be negative."))

    # ---------------------------------------------------------
    # Contact Creation
    # ---------------------------------------------------------

    def _prepare_intern_contact_vals(self):
        self.ensure_one()

        full_name = self._get_intern_full_name() or self.partner_name
        Partner = self.env["res.partner"]

        vals = {
            "name": full_name,
            "email": self.email_from or False,
            "phone": self.partner_phone or False,
            "company_type": "person",
            "type": "contact",
            "company_id": self.company_id.id if self.company_id else False,
        }

        if "mobile" in Partner._fields:
            vals["mobile"] = self.partner_phone or False

        if self.job_id and "function" in Partner._fields:
            vals["function"] = self.job_id.name

        if "linkedin_profile" in Partner._fields and self.linkedin_profile:
            vals["linkedin_profile"] = self.linkedin_profile

        if "comment" in Partner._fields:
            comment_parts = [
                _("Created from Intern Recruitment."),
                _("Intern Reference: %s") % (self.intern_reference or ""),
            ]

            if self.job_id:
                comment_parts.append(
                    _("Intern Job Position: %s") % self.job_id.name
                )

            if self.pan_number:
                comment_parts.append(_("PAN Number: %s") % self.pan_number)

            if self.degree_id:
                comment_parts.append(_("Degree: %s") % self.degree_id.name)

            if self.stream_id:
                comment_parts.append(_("Stream: %s") % self.stream_id.name)

            if self.university_id:
                comment_parts.append(_("University: %s") % self.university_id.name)

            vals["comment"] = "\n".join(comment_parts)

        return vals

    def _create_or_update_intern_contact(self):
        self.ensure_one()

        contact_vals = self._prepare_intern_contact_vals()

        if self.partner_id:
            self.partner_id.sudo().write(contact_vals)
            contact = self.partner_id
        else:
            contact = self.env["res.partner"].sudo().create(contact_vals)
            self.with_context(allow_intern_stage_change=True).sudo().write(
                {"partner_id": contact.id}
            )

        return contact

    # ---------------------------------------------------------
    # Workflow History
    # ---------------------------------------------------------

    def _create_intern_workflow_history(
        self,
        old_stage=False,
        new_stage=False,
        action_type="approved",
        remarks=False,
    ):
        history_obj = self.env["intern.workflow.history"].sudo()

        for applicant in self:
            history_obj.create(
                {
                    "applicant_id": applicant.id,
                    "old_stage_id": old_stage.id if old_stage else False,
                    "new_stage_id": new_stage.id if new_stage else False,
                    "action_type": action_type,
                    "remarks": remarks or False,
                }
            )

    # ---------------------------------------------------------
    # Workflow Movement
    # ---------------------------------------------------------

    def _check_intern_manager_access(self):
        if self.env.user.has_group("base.group_system"):
            return True

        if self.env.user.has_group(
            "recruitment_stages_status_enhancement.group_intern_recruitment_manager"
        ):
            return True

        raise UserError(
            _("Only Intern Recruitment Managers can change intern workflow stages.")
        )

    def _move_to_intern_stage(self, new_stage, action_type, remarks=False):
        for applicant in self:
            if not applicant.stage_id:
                raise UserError(_("The intern applicant does not have a current stage."))

            if not new_stage:
                raise UserError(_("No valid stage is configured."))

            old_stage = applicant.stage_id

            applicant.with_context(allow_intern_stage_change=True).write(
                {
                    "stage_id": new_stage.id,
                }
            )

            if new_stage.intern_rejected_stage:
                applicant.application_status = "rejected"
            elif new_stage.intern_final_stage:
                applicant.application_status = "completed"
                applicant.date_closed = fields.Datetime.now()
            elif new_stage.intern_create_employee_stage or new_stage.intern_is_post_hiring_stage:
                applicant.application_status = "hired"
                if not applicant.date_closed:
                    applicant.date_closed = fields.Datetime.now()
            else:
                applicant.application_status = "ongoing"

            applicant._create_intern_workflow_history(
                old_stage=old_stage,
                new_stage=new_stage,
                action_type=action_type,
                remarks=remarks,
            )

            applicant.message_post(
                body=_("Intern workflow moved from <b>%s</b> to <b>%s</b>.")
                % (old_stage.name, new_stage.name)
            )

    def action_intern_approve(self):
        self._check_intern_manager_access()

        for applicant in self:
            current_stage = applicant.stage_id

            if not current_stage:
                raise UserError(_("This applicant is not in a valid workflow stage."))

            next_stage = current_stage.get_next_intern_stage()

            if not next_stage:
                raise UserError(
                    _("No next stage is configured for '%s'.") % current_stage.name
                )

            applicant._move_to_intern_stage(
                new_stage=next_stage,
                action_type="approved",
                remarks=_("Moved to the next stage."),
            )

        return True

    def action_intern_send_back(self):
        self._check_intern_manager_access()

        for applicant in self:
            current_stage = applicant.stage_id

            if not current_stage:
                raise UserError(_("This applicant is not in a valid workflow stage."))

            if not current_stage.intern_allow_send_back:
                raise UserError(
                    _("Move to Previous Stage is not allowed from '%s'.")
                    % current_stage.name
                )

            previous_stage = current_stage.get_previous_intern_stage()

            if not previous_stage:
                raise UserError(
                    _("No previous stage is configured for '%s'.")
                    % current_stage.name
                )

            applicant._move_to_intern_stage(
                new_stage=previous_stage,
                action_type="sent_back",
                remarks=_("Moved to the previous stage."),
            )

        return True

    def action_intern_reject(self):
        self._check_intern_manager_access()

        rejected_stage = self.env["intern.recruitment.stage"].get_rejected_intern_stage()

        if not rejected_stage:
            raise UserError(_("Please configure one rejected intern stage first."))

        for applicant in self:
            current_stage = applicant.stage_id

            if not current_stage:
                raise UserError(_("This applicant is not in a valid workflow stage."))

            if not current_stage.intern_allow_reject:
                raise UserError(
                    _("Reject is not allowed from '%s'.") % current_stage.name
                )

            applicant._move_to_intern_stage(
                new_stage=rejected_stage,
                action_type="rejected",
                remarks=_("Intern applicant rejected."),
            )

        return True

    # ---------------------------------------------------------
    # Employee Creation
    # ---------------------------------------------------------

    def _prepare_employee_vals(self, contact):
        self.ensure_one()

        full_name = self._get_intern_full_name() or self.partner_name
        Employee = self.env["hr.employee"]

        vals = {
            "name": full_name,
        }

        if "first_name" in Employee._fields:
            vals["first_name"] = self.intern_first_name or False

        if "middle_name" in Employee._fields:
            vals["middle_name"] = self.intern_middle_name or False

        if "last_name" in Employee._fields:
            vals["last_name"] = self.intern_last_name or False

        if "employee_first_name" in Employee._fields:
            vals["employee_first_name"] = self.intern_first_name or False

        if "employee_middle_name" in Employee._fields:
            vals["employee_middle_name"] = self.intern_middle_name or False

        if "employee_last_name" in Employee._fields:
            vals["employee_last_name"] = self.intern_last_name or False

        if "work_email" in Employee._fields:
            vals["work_email"] = self.email_from or False

        if "work_phone" in Employee._fields:
            vals["work_phone"] = self.partner_phone or False

        if "mobile_phone" in Employee._fields:
            vals["mobile_phone"] = self.partner_phone or False

        if "job_title" in Employee._fields and self.job_id:
            vals["job_title"] = self.job_id.name

        if "department_id" in Employee._fields and self.department_id:
            vals["department_id"] = self.department_id.id

        if "company_id" in Employee._fields and self.company_id:
            vals["company_id"] = self.company_id.id

        if contact:
            if "work_contact_id" in Employee._fields:
                vals["work_contact_id"] = contact.id

            if "address_home_id" in Employee._fields:
                vals["address_home_id"] = contact.id

        if "intern_applicant_id" in Employee._fields:
            vals["intern_applicant_id"] = self.id

        if "intern_job_id" in Employee._fields and self.job_id:
            vals["intern_job_id"] = self.job_id.id

        if "pan_number" in Employee._fields:
            vals["pan_number"] = self.pan_number or False

        if "degree_id" in Employee._fields and self.degree_id:
            vals["degree_id"] = self.degree_id.id

        if "stream_id" in Employee._fields and self.stream_id:
            vals["stream_id"] = self.stream_id.id

        if "university_id" in Employee._fields and self.university_id:
            vals["university_id"] = self.university_id.id

        if "is_intern_employee" in Employee._fields:
            vals["is_intern_employee"] = True

        if "intern_source" in Employee._fields:
            vals["intern_source"] = "intern_recruitment"

        if "resume_doc" in Employee._fields and self.resume_file:
            vals["resume_doc"] = self.resume_file

        if "resume_filename" in Employee._fields and self.resume_filename:
            vals["resume_filename"] = self.resume_filename

        return vals

    def create_employee_from_applicant(self):
        self.ensure_one()
        self._check_intern_manager_access()
        self._validate_intern_required_fields()

        if self.employee_id:
            raise UserError(
                _("An employee record is already linked to this intern applicant.")
            )

        if not self.stage_id or not self.stage_id.intern_create_employee_stage:
            raise UserError(
                _(
                    "You can create an employee only when the intern applicant reaches "
                    "a stage configured as 'Create Employee Stage'."
                )
            )

        contact = self._create_or_update_intern_contact()
        employee_vals = self._prepare_employee_vals(contact)

        employee = self.env["hr.employee"].sudo().create(employee_vals)

        self.with_context(allow_intern_stage_change=True).sudo().write(
            {
                "employee_id": employee.id,
                "application_status": "hired",
                "date_closed": fields.Datetime.now(),
            }
        )

        self._create_intern_workflow_history(
            old_stage=self.stage_id,
            new_stage=self.stage_id,
            action_type="employee_created",
            remarks=_("Employee and contact records created from intern applicant."),
        )

        self.message_post(
            body=_(
                "Employee record and contact record created for this intern applicant."
            )
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Intern Employee"),
            "res_model": "hr.employee",
            "view_mode": "form",
            "res_id": employee.id,
            "target": "current",
            "context": {
                "default_is_intern_employee": True,
                "intern_employee_view": True,
            },
        }