# -*- coding: utf-8 -*-

import logging

from odoo import api, models
from odoo.http import request

_logger = logging.getLogger(__name__)

# Cookie names (must match models/ir_http.py)
REFERRAL_COOKIE_PARTNER = "social_share_ref"
REFERRAL_COOKIE_TYPE = "social_share_ref_type"
REFERRAL_COOKIE_SOURCE = "social_share_ref_source_id"


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Reward BLOG referrals when a visitor who followed a shared
        blog link creates a website account.

        Blog posts have no "checkout" or "registration" step the way
        Events (event.registration) or the Shop (sale.order) do - the
        closest equivalent action a referred reader can take is signing
        up for an account on the website. So, unlike the event and
        product flows (which reward on registration/purchase
        confirmation), the blog reward is granted as soon as the new
        account is created, provided the referral cookie is present and
        marks the visit as coming from a blog share.
        """
        users = super().create(vals_list)

        # Customer Signup reward: a flat, one-time, non-shareable "thanks
        # for joining" grant to the new account holder themselves - fully
        # independent of the blog-referral flow below (that rewards
        # whoever REFERRED them; this rewards THEM, and never involves a
        # referral cookie, a referrer, or any further sharing at all).
        # Idempotency (never more than once per partner) is enforced by
        # res.partner.signup_reward_granted, checked inside the handler -
        # see handlers/customer_signup.py.
        from ..services.reward_service import RewardService

        for user in users:
            partner = user.partner_id
            if not partner:
                continue
            RewardService.grant_signup_reward(self.env, partner)

        try:
            cookie_type = request.httprequest.cookies.get(REFERRAL_COOKIE_TYPE)
            cookie_partner = request.httprequest.cookies.get(REFERRAL_COOKIE_PARTNER)
            cookie_source = request.httprequest.cookies.get(REFERRAL_COOKIE_SOURCE)
        except RuntimeError:
            # No active HTTP request (backend user creation, cron, import,
            # data loading...) - nothing to attribute.
            return users

        if cookie_type != "blog" or not cookie_partner:
            return users

        try:
            referrer_partner = (
                self.env["res.partner"].sudo().browse(int(cookie_partner)).exists()
            )
        except (ValueError, TypeError):
            return users

        if not referrer_partner:
            return users

        ICP = self.env["ir.config_parameter"].sudo()

        enabled = ICP.get_param(
            "social_sharing_loyalty_points_enhancement.enable_blog_referral_rewards",
            default="True",
        )

        if enabled != "True":
            return users

        from ..services.reward_service import RewardService

        blog_post_id = False
        try:
            if cookie_source:
                blog_post_id = int(cookie_source)
        except (ValueError, TypeError):
            blog_post_id = False

        for user in users:

            partner = user.partner_id

            if not partner or partner == referrer_partner:
                # No self-referral.
                continue

            referral = RewardService.register_referral(
                self.env,
                "blog",
                referrer_partner,
                partner,
                blog_post_id=blog_post_id or False,
            )

            if not referral:
                # Safely ignored (feature disabled / no handler or
                # program configured / already rewarded / validation
                # failed) - account creation itself is unaffected.
                continue

            _logger.info(
                "Blog referral eligible (pending claim): %s referred %s "
                "via new account signup.",
                referrer_partner.display_name,
                partner.display_name,
            )

        return users