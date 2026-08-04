# -*- coding: utf-8 -*-
"""
Shared logic for the three "referral converts -> get points" handlers
(event_referral, product_referral, blog_referral).

social.referral.record already auto-claims itself the moment it is
created (see models/referral_record.py create()), including reversing
any earlier matching Share Reward - that behaviour is unchanged by this
refactor. What used to live inline in event_registration.py /
sale_order.py / res_users.py (reading ir.config_parameter, building the
vals dict, checking for an existing record) now lives here once, shared
by all three referral triggers.
"""

from .base_handler import BaseRewardHandler


class BaseReferralHandler(BaseRewardHandler):
    """Common implementation for every "referral converted" reward.
    Subclasses: handlers/event_referral.py, handlers/product_referral.py,
    handlers/blog_referral.py.
    """

    #: 'event' | 'product' | 'blog' - must match
    #: social.referral.record's referral_type selection.
    referral_type = None

    #: field on social.referral.record that uniquely identifies a single
    #: occurrence of this referral type, if any (e.g. one registration
    #: can only ever produce one event referral). Product/blog referrals
    #: have no such single-field key, so this stays None for them and
    #: uniqueness is instead checked on (referrer, referred) below.
    unique_key_field = None

    #: A duplicate referral is not an error - it's the same conversion
    #: being reported twice (e.g. a visitor re-clicking a shared link,
    #: or the same registration/order event firing more than once).
    #: execute() below already handles this idempotently by returning
    #: the pre-existing record instead of creating a second one, so the
    #: validation pipeline must let it through rather than rejecting it
    #: as ineligible (see BaseRewardHandler.IDEMPOTENT_REASONS).
    IDEMPOTENT_REASONS = frozenset({"duplicate_referral"})

    def is_eligible(self, program, referrer_partner=None,
                     referred_partner=None, **context):
        if not referrer_partner or not referred_partner:
            return False, "missing_partner"

        if not referrer_partner.active or not referred_partner.active:
            return False, "partner_inactive"

        if referrer_partner.id == referred_partner.id:
            # Self Referral Prevention
            return False, "self_referral_prevented"

        # Duplicate Prevention
        if self._find_existing(referrer_partner, referred_partner, **context):
            return False, "duplicate_referral"

        return True, None

    def _find_existing(self, referrer_partner, referred_partner, **context):
        ReferralRecord = self.env["social.referral.record"].sudo()

        if self.unique_key_field and context.get(self.unique_key_field):
            return ReferralRecord.search([
                (self.unique_key_field, "=", context[self.unique_key_field]),
            ], limit=1)

        return ReferralRecord.search([
            ("referral_type", "=", self.referral_type),
            ("referrer_partner_id", "=", referrer_partner.id),
            ("referred_partner_id", "=", referred_partner.id),
        ], limit=1)

    def execute(self, program, referrer_partner=None, referred_partner=None,
                points_override=None, **context):
        ReferralRecord = self.env["social.referral.record"].sudo()

        existing = self._find_existing(referrer_partner, referred_partner, **context)
        if existing:
            return existing

        points = points_override if points_override is not None else program.reward_trigger_points

        vals = {
            "referral_type": self.referral_type,
            "referrer_partner_id": referrer_partner.id,
            "referred_partner_id": referred_partner.id,
            "loyalty_program_id": program.id,
            "rewarded_points": points,
            "state": "pending",
        }

        # Only pass through the context keys that social.referral.record
        # actually has fields for, so callers can pass extra bookkeeping
        # kwargs (already consumed above) without them leaking into
        # create() and raising "invalid field" errors.
        allowed_extra = (
            "registration_id", "sale_order_id", "product_id", "blog_post_id",
        )
        for key in allowed_extra:
            if context.get(key):
                vals[key] = context[key]

        # NOTE: social.referral.record.create() already auto-claims the
        # reward (credits the loyalty card, reverses any matching Share
        # Reward) - see models/referral_record.py. We must not call
        # action_claim() again here.
        return ReferralRecord.create(vals)