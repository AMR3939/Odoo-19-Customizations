from odoo import models, fields, api

class HrEmployeePlaceOfBirth(models.Model):
    _name = 'hr.employee.place_of_birth'
    _description = 'Place of Birth'
    _rec_name = 'display_name'
    _order = 'display_name'

    # The 'options' parameter has been removed as it's not a valid Python parameter
    city_id = fields.Many2one('res.city', string='City', required=True)
    state_id = fields.Many2one(related='city_id.state_id', store=True, readonly=True)
    country_id = fields.Many2one(related='city_id.country_id', store=True, readonly=True)
    display_name = fields.Char(string='Place of Birth', compute='_compute_display_name', store=True)

    @api.depends('city_id.name', 'state_id.name')
    def _compute_display_name(self):
        for record in self:
            parts = [p for p in (record.city_id.name, record.state_id.name) if p]
            record.display_name = ", ".join(parts)