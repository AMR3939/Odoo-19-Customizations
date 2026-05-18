from odoo import models, fields

class HrEmployeeDegree(models.Model):
    _name = 'hr.employee.degree'
    _description = 'Employee Degree'
    _order = 'name'

    name = fields.Char(string='Degree', required=True, translate=True)
