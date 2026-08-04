from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points_total = fields.Float(
        string='Total Loyalty Points',
        compute='_compute_loyalty_points_total',
        store=False,
    )

    def _compute_loyalty_points_total(self):
        domain = [
            ('partner_id', 'in', self.ids),
            ('program_id.program_type', 'in', ['loyalty', 'gift_card', 'ewallet']),
        ]

        # Fetch ALL cards for ALL partners in self in ONE single query
        # instead of one query per partner (N+1 problem).
        all_cards = self.env['loyalty.card'].sudo().search(domain)

        # Group points by partner_id in memory — no extra DB calls
        points_by_partner = {}
        for card in all_cards:
            pid = card.partner_id.id
            points_by_partner[pid] = points_by_partner.get(pid, 0.0) + card.points

        for partner in self:
            partner.loyalty_points_total = points_by_partner.get(partner.id, 0.0)
