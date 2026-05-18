from odoo import models, fields

class ResUniversity(models.Model):
    _name = 'res.university'
    _description = 'University'
    _order = 'name'

    name = fields.Char(string='University Name', required=True)
    city_id = fields.Many2one('res.city', string='City', required=True) # ADDED required=True
    country_id = fields.Many2one(related='city_id.country_id',
                                 string='Country', readonly=True, store=True)