# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

# Must match the cookie names used in models/event_registration.py / ir_http.py
REFERRAL_COOKIE_NAME = "social_share_ref"
REFERRAL_COOKIE_TYPE = "social_share_ref_type"
REFERRAL_COOKIE_SOURCE = "social_share_ref_source_id"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # ------------------------------------------------------------------
    # These three fields mirror the ones already on event.registration.
    # They exist here so that a referral can be rewarded for a PLAIN
    # PRODUCT purchase - i.e. an order with no event ticket in it at all -
    # which has nowhere else to be tracked. Orders that DO contain an
    # event ticket keep using the registration-level fields/flow instead
    # (see event_registration.py); the two paths never both fire for the
    # same order (checked in action_confirm below).
    # ------------------------------------------------------------------
    referrer_partner_id = fields.Many2one(
        "res.partner",
        string="Referrer",
        copy=False,
        index=True,
        ondelete="set null",
        help="Portal user who referred this order (product-purchase "
             "referral only - event ticket orders are tracked on the "
             "event.registration record instead).",
    )

    reward_processed = fields.Boolean(
        string="Product Referral Reward Processed",
        default=False,
        copy=False,
        readonly=True,
    )

    referral_record_id = fields.Many2one(
        "social.referral.record",
        string="Referral Record",
        copy=False,
        readonly=True,
        ondelete="set null",
    )

    referral_source_product_id = fields.Many2one(
        "product.product",
        string="Referred Via Product",
        copy=False,
        readonly=True,
        ondelete="set null",
        help="The exact product page that was shared to generate this "
             "referral, captured from the referral cookie at order-creation "
             "time. Stored so the eventual product-referral record can be "
             "matched back, exactly, to the sharer's earlier Share Reward "
             "for the same product (see social.referral.record."
             "_reverse_matching_share_reward()), instead of relying on a "
             "fuzzy name comparison.",
    )

    def _capture_referral_from_cookie(self):
        """
        Reads the referral cookies (if present) and sets
        referrer_partner_id / referral_source_product_id on any order in
        `self` that doesn't have them yet. Safe to call more than once -
        every check is `if order.referrer_partner_id: continue` first, so
        an order that's already captured is left untouched.

        WHY THIS EXISTS AS ITS OWN METHOD, called from BOTH create() AND
        action_confirm(): website_sale reuses a single draft sale.order as
        a visitor's cart for their whole session - it does NOT create a
        fresh order every time something is added to cart. If the visitor
        already had an order/cart from earlier in the session (e.g. they
        browsed the shop and added something before ever clicking a
        referral link), create() never fires again for that same order,
        so relying on create() alone means the referral is silently lost
        even though the referral cookie is legitimately present by the
        time they check out. Re-checking at action_confirm() time closes
        that gap: cookies persist for the cookie's full lifetime (see
        ir_http.py), so as long as the visitor followed the referral link
        at ANY point in this browsing session before confirming, the
        cookie is still there to be read here, even if it arrived after
        the cart already existed.
        """
        try:
            cookie_value = request.httprequest.cookies.get(REFERRAL_COOKIE_NAME)
            cookie_type = request.httprequest.cookies.get(REFERRAL_COOKIE_TYPE)
            cookie_source = request.httprequest.cookies.get(REFERRAL_COOKIE_SOURCE)
        except RuntimeError:
            return

        if not cookie_value:
            return

        try:
            referrer_partner = (
                self.env["res.partner"].sudo().browse(int(cookie_value)).exists()
            )
        except (ValueError, TypeError):
            referrer_partner = False

        if not referrer_partner:
            return

        # Only trust the source id as a product id when the cookie says the
        # referral actually came from a product-page share.
        source_product = False
        if cookie_type == "product" and cookie_source:
            try:
                source_product = (
                    self.env["product.product"].sudo().browse(int(cookie_source)).exists()
                )
            except (ValueError, TypeError):
                source_product = False

        for order in self:

            if order.referrer_partner_id:
                continue

            if order.partner_id == referrer_partner:
                # Prevent self-referral.
                continue

            order.referrer_partner_id = referrer_partner.id

            if source_product:
                order.referral_source_product_id = source_product.id

    @api.model_create_multi
    def create(self, vals_list):
        """
        Capture the referrer for orders that are pure product purchases
        (no event registration involved). Same cookie-based fallback
        pattern as event_registration.py's create() override.

        This is the EARLY capture point - see _capture_referral_from_cookie()
        for why action_confirm() also re-checks as a fallback for carts
        that already existed before the referral cookie was set.
        """
        orders = super().create(vals_list)
        orders._capture_referral_from_cookie()
        return orders

    def action_confirm(self):
        """
        Grants two DIFFERENT kinds of referral rewards on confirmation:

        1. Event-ticket referrals (unchanged from before) - a fallback
           for any event.registration that didn't get its reward created
           at registration-creation time already.
        2. Product-purchase referrals (new) - for orders that don't
           contain an event ticket at all, reward the referrer directly
           off the order itself using the fields added above.

        An order is only ever processed by ONE of these two paths -
        if it contains an event registration, path 2 is skipped for it,
        since path 1 (or event_registration.py's create()) already
        covers it. This prevents a single event-ticket order from ever
        earning a referral reward twice.
        """
        res = super().action_confirm()

        ICP = self.env["ir.config_parameter"].sudo()

        # Event and Product referral now have their own independent
        # switches (mirroring the Social Sharing per-type split) -
        # disabling one must never disable the other, so each path
        # below checks its own flag instead of one combined early exit.
        event_referral_enabled = ICP.get_param(
            "social_sharing_loyalty_points_enhancement.enable_event_referral_rewards",
            default="True",
        ) == "True"
        product_referral_enabled = ICP.get_param(
            "social_sharing_loyalty_points_enhancement.enable_product_referral_rewards",
            default="True",
        ) == "True"

        if not event_referral_enabled and not product_referral_enabled:
            return res

        from ..services.reward_service import RewardService

        ReferralRecord = self.env["social.referral.record"].sudo()

        for order in self:

            has_event_line = any(
                getattr(line, "event_id", False) for line in order.order_line
            )

            # ---------------------------------------------------------
            # PATH 1 - event ticket orders (existing behaviour, fallback
            # only - normally already handled at registration-creation
            # time by event_registration.py). Skipped entirely when the
            # Event Referral switch is off - the actual reward is also
            # re-checked per-trigger inside RewardService.register_referral()
            # regardless, this just avoids the DB search below when it's
            # not going to lead anywhere.
            # ---------------------------------------------------------
            registrations = self.env["event.registration"].sudo().search([
                ("sale_order_id", "=", order.id),
                ("state", "!=", "cancel"),
                ("reward_processed", "=", False),
                ("referrer_partner_id", "!=", False),
            ]) if event_referral_enabled else self.env["event.registration"]

            for registration in registrations:

                referrer = registration.referrer_partner_id

                if not referrer:
                    continue

                if registration.partner_id == referrer:
                    _logger.info(
                        "Self referral prevented for registration %s",
                        registration.id,
                    )
                    continue

                existing = ReferralRecord.search(
                    [("registration_id", "=", registration.id)],
                    limit=1,
                )

                if existing:
                    registration.reward_processed = True
                    continue

                referral = RewardService.register_referral(
                    self.env,
                    "event",
                    referrer,
                    registration.partner_id,
                    registration_id=registration.id,
                    sale_order_id=order.id,
                )

                if not referral:
                    # Safely ignored (feature disabled / no handler or
                    # program configured / validation failed).
                    continue

                # NOTE: social.referral.record's create() override already
                # auto-claims the reward - RewardService never calls
                # action_claim() again itself, the record is already
                # state='rewarded' by now.

                registration.write({
                    "reward_processed": True,
                    "referral_record_id": referral.id,
                })

                _logger.info(
                    "Referral eligible (pending claim): %s referred %s",
                    referrer.display_name,
                    registration.partner_id.display_name,
                )

            # ---------------------------------------------------------
            # PATH 2 - plain product orders (new). Skipped entirely for
            # orders that contain an event ticket, since those are
            # already covered by Path 1 above, and skipped when the
            # Product Referral switch is off.
            # ---------------------------------------------------------
            if has_event_line or not product_referral_enabled:
                continue

            if order.reward_processed:
                continue

            # Fallback capture: closes the gap where this order/cart
            # already existed (from earlier browsing) before the visitor
            # ever followed the referral link - see
            # _capture_referral_from_cookie() for why. No-ops instantly
            # if referrer_partner_id is already set from create().
            if not order.referrer_partner_id:
                order._capture_referral_from_cookie()

            referrer = order.referrer_partner_id

            if not referrer:
                continue

            if order.partner_id == referrer:
                _logger.info(
                    "Self referral prevented for order %s",
                    order.id,
                )
                continue

            existing = ReferralRecord.search(
                [
                    ("sale_order_id", "=", order.id),
                    ("referral_type", "=", "product"),
                ],
                limit=1,
            )

            if existing:
                order.write({
                    "reward_processed": True,
                    "referral_record_id": existing.id,
                })
                continue

            referral = RewardService.register_referral(
                self.env,
                "product",
                referrer,
                order.partner_id,
                product_id=order.referral_source_product_id.id,
                sale_order_id=order.id,
            )

            if not referral:
                # Safely ignored (feature disabled / no handler or
                # program configured / validation failed).
                continue

            # NOTE: social.referral.record's create() override already
            # auto-claims the reward - RewardService never calls
            # action_claim() again itself, the record is already
            # state='rewarded' by now.

            order.write({
                "reward_processed": True,
                "referral_record_id": referral.id,
            })

            _logger.info(
                "Product referral eligible (pending claim): %s referred %s "
                "on order %s",
                referrer.display_name,
                order.partner_id.display_name,
                order.name,
            )

        return res