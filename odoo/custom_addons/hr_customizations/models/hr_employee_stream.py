from odoo import models, fields

class HrEmployeeStream(models.Model):
    _name = 'hr.employee.stream'
    _description = 'Employee Stream (Field of Study)'
    _order = 'name'

    name = fields.Char(string='Stream', required=True, translate=True)