from odoo import models, fields, api

class HrEmployeeUniversity(models.Model):
    _name = 'hr.employee.university'
    _description = 'Employee University'
    _rec_name = 'display_name'
    _order = 'name'

    name = fields.Char(string='University Name', required=True)
    city_id = fields.Many2one('res.city', string='City')
    state_id = fields.Many2one(related='city_id.state_id', store=True, readonly=True)
    country_id = fields.Many2one(related='city_id.country_id', store=True, readonly=True)
    display_name = fields.Char(string='University', compute='_compute_display_name', store=True)

    # THIS IS THE FIX: The display name is now "University Name, State, Country"
    @api.depends('name', 'state_id.name', 'country_id.name')
    def _compute_display_name(self):
        for record in self:
            parts = [p for p in (record.name, record.state_id.name, record.country_id.name) if p]
            record.display_name = ", ".join(parts)