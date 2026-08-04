# -*- coding: utf-8 -*-
"""
Extends Website Event's free-attendee registration flow to attach the
referrer to each attendee at creation time.

Note: models/event_registration.py's create() override already reads
the referral cookie directly as a fallback for ANY registration
creation path (including this one), so functionality does not strictly
depend on this controller. It is restored anyway for parity with that
model's own docstring and so the "quick" free-registration form
attaches the referrer immediately, before create() even runs, rather
than relying purely on the fallback.
"""

from odoo.http import request
from odoo.addons.website_event_sale.controllers.main import WebsiteEventSaleController

REFERRAL_COOKIE_NAME = "social_share_ref"


class WebsiteEventReferralController(WebsiteEventSaleController):

    def _create_attendees_from_registration_post(self, event, registration_data):
        cookie_value = request.httprequest.cookies.get(REFERRAL_COOKIE_NAME)

        if cookie_value:
            try:
                referrer_partner = (
                    request.env["res.partner"].sudo().browse(int(cookie_value)).exists()
                )
            except (ValueError, TypeError):
                referrer_partner = False

            if referrer_partner:
                for registration in registration_data:
                    partner_id = registration.get("partner_id")

                    # Prevent self-referral.
                    if partner_id and partner_id == referrer_partner.id:
                        continue

                    registration["referrer_partner_id"] = referrer_partner.id

        return super()._create_attendees_from_registration_post(
            event, registration_data,
        )
