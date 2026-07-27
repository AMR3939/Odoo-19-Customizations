# -*- coding: utf-8 -*-

import base64
import logging
from urllib.parse import urlencode

from werkzeug.utils import secure_filename

from odoo import http, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)


class InternRecruitmentWebsite(http.Controller):
    """
    Website controller for the independent Intern Recruitment module.

    Routes:
        /intern/jobs
        /intern/jobs/<job_id>
        /intern/jobs/<job_id>/apply
        /intern/jobs/<job_id>/apply/submit
        /intern/apply/success
    """

    # ---------------------------------------------------------
    # General Helpers
    # ---------------------------------------------------------

    def _get_published_job(self, job_id):
        """Return an active and published intern job."""

        return request.env["intern.job"].sudo().search(
            [
                ("id", "=", job_id),
                ("active", "=", True),
                ("website_published", "=", True),
            ],
            limit=1,
        )

    def _clean_text(self, value):
        """Remove leading and trailing whitespace."""

        return (value or "").strip()

    def _clean_pan(self, value):
        """Remove whitespace and convert PAN number to uppercase."""

        return self._clean_text(value).upper()

    def _safe_float(self, value):
        """Convert a submitted value to float safely."""

        value = self._clean_text(value)

        if not value:
            return 0.0

        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValidationError(
                _("Expected stipend must be a valid number.")
            )

    def _get_error_message(self, exception):
        """Extract a user-friendly message from an exception."""

        if hasattr(exception, "name") and exception.name:
            return exception.name

        if exception.args:
            return exception.args[0]

        return str(exception)

    def _get_apply_form_values(self):
        """
        The website form uses text inputs instead of dropdowns.

        This method is retained so that the form rendering flow remains
        consistent and can be extended later.
        """

        return {}

    # ---------------------------------------------------------
    # Education Mapping Helpers
    # ---------------------------------------------------------

    def _get_or_create_simple_record(
        self,
        model_name,
        name,
        field_label,
        required=False,
    ):
        """
        Find or create a simple record that contains a name field.

        Used for:
            hr.employee.degree
            hr.employee.stream
        """

        name = self._clean_text(name)

        if not name:
            if required:
                raise ValidationError(
                    _("Please enter %s.") % field_label
                )

            return False

        Model = request.env[model_name].sudo()

        record = Model.search(
            [
                ("name", "=ilike", name),
            ],
            limit=1,
        )

        if record:
            return record.id

        record = Model.create(
            {
                "name": name,
            }
        )

        return record.id

    def _get_country_from_text(self, country_text, required=False):
        """
        Find an existing country using its name or country code.

        Countries are not created automatically because Odoo already
        provides country master data.
        """

        country_text = self._clean_text(country_text)

        if not country_text:
            if required:
                raise ValidationError(
                    _("Please enter University Country.")
                )

            return False

        Country = request.env["res.country"].sudo()

        country = Country.search(
            [
                ("name", "=ilike", country_text),
            ],
            limit=1,
        )

        if not country and len(country_text) in (2, 3):
            country = Country.search(
                [
                    ("code", "=ilike", country_text.upper()),
                ],
                limit=1,
            )

        if not country:
            raise ValidationError(
                _(
                    "University Country '%s' was not found. "
                    "Please enter a valid country name, such as India."
                )
                % country_text
            )

        return country.id

    def _get_state_from_text(
        self,
        state_text,
        country_id,
        required=False,
    ):
        """
        Find an existing state by state name or state code.

        The state must belong to the submitted university country.
        """

        state_text = self._clean_text(state_text)

        if not state_text:
            if required:
                raise ValidationError(
                    _("Please enter University State.")
                )

            return False

        if not country_id:
            raise ValidationError(
                _("Please enter a valid University Country first.")
            )

        State = request.env["res.country.state"].sudo()

        state = State.search(
            [
                ("name", "=ilike", state_text),
                ("country_id", "=", country_id),
            ],
            limit=1,
        )

        if not state:
            state = State.search(
                [
                    ("code", "=ilike", state_text.upper()),
                    ("country_id", "=", country_id),
                ],
                limit=1,
            )

        if not state:
            country = request.env["res.country"].sudo().browse(country_id)

            country_name = (
                country.name
                if country.exists()
                else _("the selected country")
            )

            raise ValidationError(
                _(
                    "University State '%(state)s' was not found in "
                    "%(country)s. Please enter a valid state name, "
                    "such as Kerala."
                )
                % {
                    "state": state_text,
                    "country": country_name,
                }
            )

        return state.id

    def _get_or_create_city_from_text(
        self,
        city_text,
        country_id=False,
        state_id=False,
        required=False,
    ):
        """
        Find or create a city.

        state_id is required because the res.city table in this database
        has a required state_id field.
        """

        city_text = self._clean_text(city_text)

        if not city_text:
            if required:
                raise ValidationError(
                    _("Please enter University City.")
                )

            return False

        if not state_id:
            raise ValidationError(
                _("Please enter a valid University State.")
            )

        City = request.env["res.city"].sudo()

        domain = [
            ("name", "=ilike", city_text),
        ]

        if "state_id" in City._fields:
            domain.append(
                ("state_id", "=", state_id)
            )

        if country_id and "country_id" in City._fields:
            domain.append(
                ("country_id", "=", country_id)
            )

        city = City.search(
            domain,
            limit=1,
        )

        if city:
            return city.id

        vals = {
            "name": city_text,
        }

        if "state_id" in City._fields:
            vals["state_id"] = state_id

        if country_id and "country_id" in City._fields:
            vals["country_id"] = country_id

        city = City.create(vals)

        return city.id

    def _get_or_create_university_record(
        self,
        university_text,
        university_city_text,
        university_state_text,
        university_country_text,
        required=False,
    ):
        """
        Find or create an employee university record.

        Mapping:
            Country text
                -> res.country

            State text
                -> res.country.state

            City text
                -> res.city

            University text
                -> hr.employee.university
        """

        university_text = self._clean_text(university_text)
        university_city_text = self._clean_text(
            university_city_text
        )
        university_state_text = self._clean_text(
            university_state_text
        )
        university_country_text = self._clean_text(
            university_country_text
        )

        if not university_text:
            if required:
                raise ValidationError(
                    _("Please enter University.")
                )

            return False

        if not university_city_text:
            raise ValidationError(
                _("Please enter University City.")
            )

        if not university_state_text:
            raise ValidationError(
                _("Please enter University State.")
            )

        if not university_country_text:
            raise ValidationError(
                _("Please enter University Country.")
            )

        country_id = self._get_country_from_text(
            university_country_text,
            required=True,
        )

        state_id = self._get_state_from_text(
            university_state_text,
            country_id,
            required=True,
        )

        city_id = self._get_or_create_city_from_text(
            university_city_text,
            country_id=country_id,
            state_id=state_id,
            required=True,
        )

        University = request.env[
            "hr.employee.university"
        ].sudo()

        university = University.search(
            [
                ("name", "=ilike", university_text),
                ("city_id", "=", city_id),
            ],
            limit=1,
        )

        if university:
            return university.id

        university = University.create(
            {
                "name": university_text,
                "city_id": city_id,
            }
        )

        return university.id

    # ---------------------------------------------------------
    # Resume Helpers
    # ---------------------------------------------------------

    def _prepare_resume_vals(self, post):
        """Validate and encode the uploaded resume."""

        resume = post.get("resume_file")

        if not resume:
            raise ValidationError(
                _("Please upload your resume.")
            )

        filename = secure_filename(
            resume.filename or ""
        )

        if not filename:
            raise ValidationError(
                _("Please upload a valid resume file.")
            )

        if not filename.lower().endswith(".pdf"):
            raise ValidationError(
                _("Resume must be a PDF file.")
            )

        file_content = resume.read()

        if not file_content:
            raise ValidationError(
                _("Uploaded resume file is empty.")
            )

        max_size = 5 * 1024 * 1024

        if len(file_content) > max_size:
            raise ValidationError(
                _("Resume file size must not exceed 5 MB.")
            )

        return {
            "resume_file": base64.b64encode(
                file_content
            ).decode("utf-8"),
            "resume_filename": filename,
        }

    # ---------------------------------------------------------
    # Website Form Processing
    # ---------------------------------------------------------

    def _redirect_apply_error(
        self,
        job,
        post,
        error_message,
    ):
        """
        Redirect to the application form and preserve entered values.

        The uploaded resume cannot be preserved after redirect, so the
        applicant must upload it again.
        """

        allowed_fields = [
            "intern_first_name",
            "intern_middle_name",
            "intern_last_name",
            "email_from",
            "partner_phone",
            "pan_number",
            "degree_text",
            "stream_text",
            "university_text",
            "university_city_text",
            "university_state_text",
            "university_country_text",
            "availability",
            "linkedin_profile",
            "salary_expected",
            "applicant_notes",
        ]

        params = {}

        for field_name in allowed_fields:
            value = post.get(field_name)

            if not value:
                continue

            if field_name == "pan_number":
                params[field_name] = self._clean_pan(value)
            else:
                params[field_name] = value

        params["error_message"] = error_message

        return request.redirect(
            "/intern/jobs/%s/apply?%s"
            % (
                job.id,
                urlencode(params),
            )
        )

    def _prepare_applicant_vals(self, job, post):
        """Prepare values for creating the intern applicant."""

        initial_stage = (
            request.env["intern.recruitment.stage"]
            .sudo()
            .get_default_intern_stage()
        )

        if not initial_stage:
            raise UserError(
                _(
                    "Please configure an initial intern workflow "
                    "stage before accepting applications."
                )
            )

        # Validate the uploaded resume before creating any education
        # master records.
        resume_vals = self._prepare_resume_vals(post)

        degree_text = self._clean_text(
            post.get("degree_text")
        )

        stream_text = self._clean_text(
            post.get("stream_text")
        )

        university_text = self._clean_text(
            post.get("university_text")
        )

        university_city_text = self._clean_text(
            post.get("university_city_text")
        )

        university_state_text = self._clean_text(
            post.get("university_state_text")
        )

        university_country_text = self._clean_text(
            post.get("university_country_text")
        )

        degree_id = self._get_or_create_simple_record(
            "hr.employee.degree",
            degree_text,
            _("Degree"),
            required=True,
        )

        stream_id = self._get_or_create_simple_record(
            "hr.employee.stream",
            stream_text,
            _("Stream"),
            required=False,
        )

        university_id = (
            self._get_or_create_university_record(
                university_text,
                university_city_text,
                university_state_text,
                university_country_text,
                required=True,
            )
        )

        vals = {
            "intern_first_name": self._clean_text(
                post.get("intern_first_name")
            ),
            "intern_middle_name": self._clean_text(
                post.get("intern_middle_name")
            ),
            "intern_last_name": self._clean_text(
                post.get("intern_last_name")
            ),
            "email_from": self._clean_text(
                post.get("email_from")
            ),
            "partner_phone": self._clean_text(
                post.get("partner_phone")
            ),
            "pan_number": self._clean_pan(
                post.get("pan_number")
            ),
            "degree_id": degree_id,
            "stream_id": stream_id,
            "university_id": university_id,
            "type_id": degree_text,
            "availability": self._clean_text(
                post.get("availability")
            ),
            "linkedin_profile": self._clean_text(
                post.get("linkedin_profile")
            ),
            "salary_expected": self._safe_float(
                post.get("salary_expected")
            ),
            "applicant_notes": self._clean_text(
                post.get("applicant_notes")
            ),
            "job_id": job.id,
            "stage_id": initial_stage.id,
        }

        vals.update(resume_vals)

        return vals

    # ---------------------------------------------------------
    # Website Pages
    # ---------------------------------------------------------

    @http.route(
        [
            "/intern/jobs",
            "/intern/jobs/",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def intern_jobs(self, **kwargs):
        """Display all active and published internship jobs."""

        jobs = request.env["intern.job"].sudo().search(
            [
                ("active", "=", True),
                ("website_published", "=", True),
            ],
            order="sequence asc, id desc",
        )

        return request.render(
            (
                "recruitment_stages_status_enhancement."
                "website_intern_jobs_list"
            ),
            {
                "jobs": jobs,
            },
        )

    @http.route(
        ["/intern/jobs/<int:job_id>"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def intern_job_detail(self, job_id, **kwargs):
        """Display the selected internship job."""

        job = self._get_published_job(job_id)

        if not job:
            return request.not_found()

        return request.render(
            (
                "recruitment_stages_status_enhancement."
                "website_intern_job_detail"
            ),
            {
                "job": job,
            },
        )

    @http.route(
        ["/intern/jobs/<int:job_id>/apply"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def intern_apply_form(self, job_id, **kwargs):
        """Display the internship application form."""

        job = self._get_published_job(job_id)

        if not job:
            return request.not_found()

        values = {
            "job": job,
        }

        values.update(
            self._get_apply_form_values()
        )

        return request.render(
            (
                "recruitment_stages_status_enhancement."
                "website_intern_apply_form"
            ),
            values,
        )

    @http.route(
        ["/intern/jobs/<int:job_id>/apply/submit"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def intern_apply_submit(self, job_id, **post):
        """Process the submitted internship application."""

        job = self._get_published_job(job_id)

        if not job:
            return request.not_found()

        try:
            vals = self._prepare_applicant_vals(
                job,
                post,
            )

            applicant = (
                request.env["intern.applicant"]
                .sudo()
                .with_context(
                    mail_create_nosubscribe=True
                )
                .create(vals)
            )

        except (ValidationError, UserError) as error:
            return self._redirect_apply_error(
                job,
                post,
                self._get_error_message(error),
            )

        except Exception:
            _logger.exception(
                "Error while submitting intern application."
            )

            return self._redirect_apply_error(
                job,
                post,
                _(
                    "Something went wrong while submitting your "
                    "application. Please try again."
                ),
            )

        return request.redirect(
            "/intern/apply/success?%s"
            % urlencode(
                {
                    "reference": (
                        applicant.intern_reference or ""
                    ),
                }
            )
        )

    @http.route(
        ["/intern/apply/success"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def intern_apply_success(self, **kwargs):
        """Display the application success page."""

        return request.render(
            (
                "recruitment_stages_status_enhancement."
                "website_intern_apply_success"
            ),
            {
                "reference": kwargs.get("reference"),
            },
        )