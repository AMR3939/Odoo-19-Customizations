# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

# Must match the cookie name used in controllers/referral.py
REFERRAL_COOKIE_NAME = "social_share_ref"


class EventRegistration(models.Model):
    _inherit = "event.registration"

    referrer_partner_id = fields.Many2one(
        "res.partner",
        string="Referrer",
        copy=False,
        index=True,
        ondelete="set null",
        help="Portal user who referred this registration.",
    )

    reward_processed = fields.Boolean(
        string="Reward Processed",
        default=False,
        copy=False,
        readonly=True,
        help="Indicates whether the referral reward has already been granted.",
    )

    referral_record_id = fields.Many2one(
        "social.referral.record",
        string="Referral Record",
        copy=False,
        readonly=True,
        ondelete="set null",
    )

    def _get_website_registration_allowed_fields(self):
        """
        Allow the website controller to pass the
        referrer_partner_id while creating registrations.
        """
        allowed_fields = super()._get_website_registration_allowed_fields()
        allowed_fields.add("referrer_partner_id")
        return allowed_fields

    @api.model_create_multi
    def create(self, vals_list):
        """
        Fallback referral capture.

        `referrer_partner_id` is normally set explicitly by
        controllers/referral.py (`_create_attendees_from_registration_post`),
        but that hook only runs for the "quick" free-attendee registration
        form. Registrations created through the paid ticket / shopping cart
        checkout flow (Shop -> Address -> Payment) never go through that
        method, so they were silently created with no referrer at all and
        the referral reward was never granted.

        This override reads the referral cookie directly, for ANY
        registration creation path, as long as an HTTP request is active
        (i.e. it was created from the website). It only fills the field in
        if it hasn't already been set upstream.
        """
        registrations = super().create(vals_list)

        try:
            cookie_value = request.httprequest.cookies.get(REFERRAL_COOKIE_NAME)
        except RuntimeError:
            # No active HTTP request (backend/cron/import) - nothing to do.
            cookie_value = None

        if not cookie_value:
            return registrations

        try:
            referrer_partner = (
                self.env["res.partner"].sudo().browse(int(cookie_value)).exists()
            )
        except (ValueError, TypeError):
            referrer_partner = False

        if not referrer_partner:
            return registrations

        for registration in registrations:

            if registration.referrer_partner_id:
                # Already captured by the free-registration flow.
                continue

            if registration.partner_id == referrer_partner:
                # Prevent self-referral.
                continue

            registration.referrer_partner_id = referrer_partner.id

            _logger.info(
                "Referral captured on registration %s for referrer %s "
                "(paid/cart registration path).",
                registration.id,
                referrer_partner.display_name,
            )

        registrations._apply_pending_referral_reward()

        return registrations

    def _apply_pending_referral_reward(self):
        """
        Create the pending social.referral.record as soon as a referred
        registration exists, instead of waiting for the related sale
        order to be paid/confirmed.

        Previously this only happened in sale_order.action_confirm()
        (see models/sale_order.py), which meant referrers had to wait
        until the referred visitor's payment was processed before their
        reward even showed up as "Pending" on /my/referrals. Calling it
        here means it happens the moment the registration itself is
        created - no need to wait on payment.

        NOTE / trade-off: for paid tickets this now grants credit for a
        registration created during checkout even if the visitor never
        completes payment (e.g. they abandon at the payment step,
        or the payment later fails). sale_order.action_confirm() is left
        in place purely as a fallback for registrations that had no
        referrer captured yet at creation time (e.g. cookie set slightly
        after the registration row was inserted); it is guarded by the
        same `reward_processed` flag so nothing is ever granted twice.
        If you'd rather only reward confirmed/paid referrals, remove
        this method call from create() and rely on action_confirm()
        alone (the original behaviour).
        """
        ICP = self.env["ir.config_parameter"].sudo()

        enabled = ICP.get_param(
            "social_sharing_loyalty_points_enhancement.enable_event_referral_rewards",
            default="True",
        )

        if enabled != "True":
            return

        from ..services.reward_service import RewardService

        for registration in self:

            if registration.state == "cancel":
                continue

            if not registration.referrer_partner_id:
                continue

            if registration.reward_processed:
                continue

            if registration.partner_id == registration.referrer_partner_id:
                # Prevent self-referral.
                continue

            referral = RewardService.register_referral(
                self.env,
                "event",
                registration.referrer_partner_id,
                registration.partner_id,
                registration_id=registration.id,
                sale_order_id=(
                    registration.sale_order_id.id
                    if registration.sale_order_id
                    else False
                ),
            )

            if not referral:
                # Safely ignored: registry validation failed (feature
                # disabled, no handler/program configured, duplicate,
                # etc). event.registration itself is left completely
                # unaffected either way.
                continue

            # NOTE: social.referral.record's own create() override already
            # auto-claims the reward (there is no manual "Claim Now" step
            # any more), so RewardService never calls action_claim() again
            # itself - the record is already state='rewarded' by this
            # point.

            registration.write({
                "reward_processed": True,
                "referral_record_id": referral.id,
            })

            _logger.info(
                "Referral eligible (pending claim) at registration time: "
                "%s referred %s",
                registration.referrer_partner_id.display_name,
                registration.partner_id.display_name,
            )