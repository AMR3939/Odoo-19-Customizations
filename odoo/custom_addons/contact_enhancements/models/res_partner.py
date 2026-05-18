from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    city_id = fields.Many2one('res.city', string='City',
                              help="Select the contact's city. State and Country will be auto-populated.")

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name
            self.state_id = self.city_id.state_id
            self.country_id = self.city_id.country_id
        else:
            self.city = False

    @api.onchange('state_id')
    def _onchange_state_id_clear_city(self):
        if self.city_id and self.city_id.state_id != self.state_id:
            self.city_id = False