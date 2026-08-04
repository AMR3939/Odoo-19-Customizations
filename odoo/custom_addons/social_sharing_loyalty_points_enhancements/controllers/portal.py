# -*- coding: utf-8 -*-
"""
Unified "My Loyalty Points" portal page (/my/loyalty) and its JSON
polling endpoint (/my/loyalty/data - see
static/src/js/loyalty_auto_refresh.js).

Read-only by design: this controller only ever reads the partner's
actual loyalty.card balance and loyalty.history ledger - the single
source of truth for points earned AND spent (redemption is 100% native
Odoo Loyalty Engine). It never decides whether/how much to reward
anyone, so none of the Registry / Handler / Validation Layer is
involved here.
"""

import json

from odoo import http
from odoo.http import request, Response
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools import format_datetime


class LoyaltyPortal(CustomerPortal):

    def _get_loyalty_values(self, partner):
        """Shared by portal_my_loyalty() (full page render) and
        portal_my_loyalty_data() (JSON polling endpoint) so the two
        never drift apart.
        """
        cards = (
            request.env["loyalty.card"]
            .sudo()
            .search([("partner_id", "=", partner.id)])
        )

        total_points = sum(cards.mapped("points"))

        histories = (
            request.env["loyalty.history"]
            .sudo()
            .search(
                [("card_id", "in", cards.ids)],
                order="create_date desc",
            )
        )

        rows = []

        for history in histories:

            points = history.issued or 0
            description = history.description or "-"

            if description.startswith("Referral Reward"):
                category = "Referral"
            elif description.startswith("Share Reward reversed"):
                category = "Share (Reversed)"
            elif description.startswith("Share Reward"):
                category = "Share"
            elif points < 0:
                category = "Redeemed"
            else:
                category = "Other"

            rows.append({
                "description": description,
                "category": category,
                "timestamp": format_datetime(
                    request.env, history.create_date, dt_format="MM/dd/yyyy hh:mm a"
                ) if history.create_date else "-",
                "points": points,
            })

        return {
            "rows": rows,
            "total_points": total_points,
        }

    @http.route(["/my/loyalty"], type="http", auth="user", website=True)
    def portal_my_loyalty(self, **kwargs):
        partner = request.env.user.partner_id
        values = self._get_loyalty_values(partner)
        values["page_name"] = "loyalty"

        return request.render(
            "social_sharing_loyalty_points_enhancement.portal_my_loyalty",
            values,
        )

    @http.route(
        ["/my/loyalty/data"],
        type="http",
        auth="user",
        website=True,
        methods=["GET"],
        csrf=False,
    )
    def portal_my_loyalty_data(self, **kwargs):
        partner = request.env.user.partner_id
        values = self._get_loyalty_values(partner)

        return Response(json.dumps(values), content_type="application/json")
