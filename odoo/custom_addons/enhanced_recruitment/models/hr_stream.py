from odoo import models, fields

class HrStream(models.Model):
    _name = 'hr.stream'
    _description = 'Applicant Stream'
    _order = 'name'

    name = fields.Char(string='Stream Name', required=True)