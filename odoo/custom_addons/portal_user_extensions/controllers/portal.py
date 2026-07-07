from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager

class PortalUserExtensions(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        # Only compute loyalty points on the initial page render (counters=[])
        # or when explicitly requested, to avoid expensive DB queries
        # during /my/counters AJAX calls.
        if not counters or 'loyalty_points_total' in counters:
            partner = request.env.user.partner_id
            values['loyalty_points_total'] = partner.loyalty_points_total
        return values

    @http.route('/my/loyalty', type='http', auth='user', website=True)
    def portal_loyalty_detail(self, page=1, **kw):
        partner = request.env.user.partner_id
        cards = request.env['loyalty.card'].sudo().search([
            ('partner_id', '=', partner.id)
        ])
        
        history = []
        for card in cards:
            for line in card.history_ids:
                points = line.issued - line.used
                history.append({
                    'date': line.create_date,
                    'description': line.description or card.program_id.name,
                    'points': points,
                    'type': 'earned' if points >= 0 else 'redeemed',
                })
                
        history.sort(key=lambda x: x['date'], reverse=True)

        # Reuse points from the cards we already fetched above —
        # avoids triggering _compute_loyalty_points_total (extra DB query).
        loyalty_points_total = sum(cards.mapped('points'))
        
        return request.render('portal_user_extensions.portal_loyalty_detail', {
            'loyalty_points_total': loyalty_points_total,
            'history': history,
            'page_name': 'loyalty',
        })
