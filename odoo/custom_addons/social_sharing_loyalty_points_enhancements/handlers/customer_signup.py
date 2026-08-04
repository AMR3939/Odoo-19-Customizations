# -*- coding: utf-8 -*-
"""
CustomerSignupHandler - a one-time, non-shareable reward granted directly
to a new customer for creating a website account.

This is deliberately NOT built on BaseShareHandler (no content was
shared) or BaseReferralHandler (no referrer is involved) - it is its own
minimal family, the third kind of reward this module supports: a flat,
unconditional "thanks for joining" grant that cannot be re-earned,
re-shared, or attributed to anyone else. See handlers/registry.py, which
has named this exact trigger ("Customer Signup") as the canonical
example of a brand-new reward type since this module's first version.
"""

from odoo import _

from .base_handler import BaseRewardHandler
from .registry import register_handler


@register_handler
class CustomerSignupHandler(BaseRewardHandler):
    """Instant, one-time reward for creating a website account.

    Unlike the Share handlers (repeatable, once per click) and the
    Referral handlers (repeatable, once per distinct referred person),
    this trigger is repeatable ZERO further times per partner after the
    first grant - "already_rewarded" is therefore in IDEMPOTENT_REASONS
    so a duplicate call (e.g. the create() hook firing twice in the same
    request) safely returns the existing grant instead of erroring, but
    never credits points twice.
    """

    trigger_code = "customer_signup"

    IDEMPOTENT_REASONS = frozenset({"already_rewarded"})

    def is_eligible(self, program, partner=None, **context):
        if not partner or not partner.id:
            return False, "no_partner"

        if not partner.active:
            return False, "partner_inactive"

        if partner.signup_reward_granted:
            return False, "already_rewarded"

        return True, None

    def execute(self, program, partner=None, points_override=None, **context):
        if not partner or not partner.id:
            return False

        # Idempotent from the caller's point of view: if the flag is
        # already set (e.g. this exact call is a duplicate/retry), there
        # is nothing left to credit or record - just report "nothing new
        # happened" rather than crediting a second time.
        if partner.signup_reward_granted:
            return False

        points = points_override if points_override is not None else program.reward_trigger_points

        description = _("Signup Reward: Welcome to %(company)s!",
                         company=self.env.company.name)

        Mixin = self.env["social.loyalty.reward.mixin"]
        Mixin._credit_loyalty_points(
            partner, program, points, description,
        )

        partner.sudo().write({"signup_reward_granted": True})

        return partner
