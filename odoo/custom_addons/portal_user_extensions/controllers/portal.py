from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class PortalUserExtensions(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        if not counters or 'loyalty_points_total' in counters:
            partner = request.env.user.partner_id
            values['loyalty_points_total'] = partner.loyalty_points_total

        return values

    @http.route('/my/loyalty', type='http', auth='user', website=True)
    def portal_loyalty_detail(self, page=1, **kw):

        partner = request.env.user.partner_id

        print("\n==============================")
        print("PORTAL LOYALTY DEBUG")
        print("==============================")
        print("Partner ID   :", partner.id)
        print("Partner Name :", partner.name)
        print("Partner Email:", partner.email)

        cards = request.env['loyalty.card'].sudo().search([
            ('partner_id', '=', partner.id)
        ])

        print("Cards Found  :", cards)
        print("Card Count   :", len(cards))

        if cards:
            for card in cards:
                print("--------------------------------")
                print("Card ID      :", card.id)
                print("Code         :", card.code)
                print("Program      :", card.program_id.name)
                print("Balance      :", card.points)
                print("History Lines:", len(card.history_ids))
        else:
            print("NO LOYALTY CARDS FOUND")

        history = []

        for card in cards:
            for line in card.history_ids:

                points = line.issued - line.used

                print(
                    f"History -> Date: {line.create_date} | "
                    f"Issued: {line.issued} | "
                    f"Used: {line.used} | "
                    f"Points: {points}"
                )

                history.append({
                    'id': line.id,
                    'date': line.create_date,
                    'description': line.description or card.program_id.name,
                    'points': points,
                    'type': 'earned' if points >= 0 else 'redeemed',
                })

        # Tiebreak on id (not points): reward/reversal pairs created in the
        # same request share an identical create_date down to the
        # microsecond, so id (creation order) is the only reliable way to
        # keep them in the sequence they actually happened.
        history.sort(
            key=lambda x: (x['date'], x['id']),
            reverse=True
        )

        loyalty_points_total = sum(cards.mapped('points'))

        print("--------------------------------")
        print("Total Points :", loyalty_points_total)
        print("History Count:", len(history))
        print("==============================\n")

        return request.render(
            'portal_user_extensions.portal_loyalty_detail',
            {
                'loyalty_points_total': loyalty_points_total,
                'history': history,
                'page_name': 'loyalty',
            }
        )