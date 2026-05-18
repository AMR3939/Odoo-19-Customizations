# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    # 1. New field for rating with help text
    custom_rating = fields.Integer(
        string='Evaluation Rating',
        help="Rate the applicant from 0 to 10."
    )

    # 2. Applicant's personal address
    applicant_city_id = fields.Many2one('res.city', string="Applicant City")
    applicant_country_id = fields.Many2one('res.country', string="Applicant Country")

    # 3. University and education details
    university_id = fields.Many2one('res.university', string="University")
    stream = fields.Many2one('hr.stream', string="Stream")

    # MODIFIED: Removed readonly=True from these two fields
    university_city_id = fields.Many2one('res.city', string="University City")
    university_country_id = fields.Many2one('res.country', string="University Country")

    university_city_filter = fields.Char(string="University City Search", store=False)

    # 4. Automation Logic & Validation
    @api.onchange('applicant_city_id')
    def _onchange_applicant_city_id(self):
        if self.applicant_city_id:
            self.applicant_country_id = self.applicant_city_id.country_id
        else:
            self.applicant_country_id = False

    @api.onchange('university_id')
    def _onchange_university_id(self):
        if self.university_id and self.university_id.city_id:
            self.university_city_id = self.university_id.city_id
            self.university_country_id = self.university_id.city_id.country_id
        else:
            self.university_city_id = False
            self.university_country_id = False

    @api.constrains('custom_rating')
    def _check_rating_range(self):
        for applicant in self:
            if applicant.custom_rating and not (0 <= applicant.custom_rating <= 10):
                raise ValidationError("The Evaluation Rating must be between 0 and 10.")