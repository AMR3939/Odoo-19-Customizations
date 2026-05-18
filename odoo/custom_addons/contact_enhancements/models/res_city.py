from odoo import models, fields, api

class ResCity(models.Model):
    _name = 'res.city'
    _description = 'City'
    _order = 'name'

    # The 'state_id' field is now defined first for the new workflow.
    state_id = fields.Many2one('res.country.state', string='State', required=True)

    # The domain on state_id has been removed.
    # The country_id is now populated by the onchange method.
    country_id = fields.Many2one('res.country', string='Country', required=True)

    name = fields.Char(string='City Name', required=True)

    _name_state_uniq = models.Constraint(
        'unique(name, state_id)',
        "City name must be unique per state!",
    )

    @api.onchange('state_id')
    def _onchange_state_id_set_country(self):
        """
        When a state is selected, automatically set the corresponding country.
        """
        if self.state_id and self.state_id.country_id:
            self.country_id = self.state_id.country_id
        else:
            self.country_id = False