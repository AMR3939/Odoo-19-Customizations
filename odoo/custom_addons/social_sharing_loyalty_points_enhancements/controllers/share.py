# -*- coding: utf-8 -*-
"""
/social_share/reward - the instant Share Reward endpoint.

Called by static/src/js/referral_share.js on every click of a website
Share button (Facebook / X / LinkedIn / Email / Copy Link), fire-and-
forget, independent of whether the shared link ever converts into a
referral.

This controller contains NO reward business logic of its own - it only
classifies the request into the two pieces of information
RewardService.grant_share_reward() needs and hands off entirely to the
Service Layer. Every safety check (feature enabled, handler registered,
program active, reward configured, customer eligible) happens inside
RewardValidationService, not here.
"""

import logging

from odoo import http
from odoo.http import request

from ..services.reward_service import RewardService
from ..services.validation_service import RewardValidationService

_logger = logging.getLogger(__name__)


class SocialShareRewardController(http.Controller):

    @http.route(
        "/social_share/reward",
        type="jsonrpc",
        auth="user",
        website=True,
        csrf=False,
    )
    def grant_share_reward(self, url=None, content_name=None, source_id=None, **kwargs):
        """auth="user" - anonymous/public visitors cannot earn share
        rewards, since points are credited to a partner's loyalty card.
        """
        user = request.env.user

        if user._is_public():
            return {
                "success": False,
                "message": "You need to be logged in to earn this reward.",
                "reason": "no_partner",
            }

        share, reason = RewardService.grant_share_reward(
            request.env,
            user.partner_id,
            url,
            content_name=content_name,
            source_id=source_id,
            return_reason=True,
        )

        if not share:
            # The native Share action/popup itself is never interrupted
            # by this - the reward is still fire-and-forget from the
            # website's point of view. `message` is only ever a short,
            # user-safe string (see validation_service.REASON_MESSAGES)
            # so nothing internal (config keys, model names, ids) is
            # ever exposed to the browser - the frontend JS shows this
            # as a small validation-error toast (see
            # static/src/js/referral_share.js). For store setup/config
            # problems (no program configured, feature disabled, etc -
            # see validation_service.SILENT_REASONS) get_user_message()
            # returns None here on purpose: those are never the
            # shopper's fault, so the JS shows nothing and the visitor
            # just sees the normal native Share popup with no toast at
            # all. The reason is still logged server-side in
            # RewardValidationService.resolve() for whoever administers
            # the site.
            return {
                "success": False,
                "message": RewardValidationService.get_user_message(reason),
                "reason": reason,
            }

        _logger.info(
            "Social Share Loyalty: granted %s share-reward points to %s",
            share.rewarded_points, user.partner_id.display_name,
        )

        return {"success": True, "points": share.rewarded_points}
