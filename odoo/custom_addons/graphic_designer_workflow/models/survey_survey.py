from odoo import models, fields, api
class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'survey_type' in fields_list:
            res['survey_type'] = 'custom'  # Set your custom default here safely
        return res

      
