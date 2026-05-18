from odoo import fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    user_degree_id = fields.Many2one(
        'hr.employee.degree',
        related='employee_id.degree_id',
        string='Degree (Employee)',
        readonly=True, # Related fields are typically readonly
        help="Employee's highest degree."
    )

    user_stream_id = fields.Many2one(
        'hr.employee.stream',
        related='employee_id.stream_id',
        string='Stream (Employee)',
        readonly=True,
        help="Employee's field of study."
    )

    user_university_id = fields.Many2one(
        'hr.employee.university',
        related='employee_id.university_id',
        string='University (Employee)',
        readonly=True,
        help="Employee's university."
    )