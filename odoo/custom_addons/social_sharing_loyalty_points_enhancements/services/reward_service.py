# -*- coding: utf-8 -*-
"""
RewardService is the single public entry point every model/controller in
this module calls to grant a reward. Nothing outside services/ and
handlers/ should ever create a social.share.record or
social.referral.record directly, or read the reward-related
ir.config_parameter keys directly - going through this service
guarantees the full validation layer always runs first.

Two public methods, matching the two families of reward in the module:

    RewardService.grant_share_reward(...)   -> instant "clicked Share"
    RewardService.register_referral(...)    -> "referral converted"
    RewardService.grant_signup_reward(...)  -> one-time "account created"
"""

import logging

from .validation_service import RewardValidationService

_logger = logging.getLogger(__name__)

#: Maps social.share.record.content_type -> reward_trigger code.
SHARE_TRIGGER_MAP = {
    "product": "product_share",
    "blog": "blog_share",
    "event": "event_share",
}

#: Maps social.referral.record.referral_type -> reward_trigger code.
REFERRAL_TRIGGER_MAP = {
    "event": "event_referral",
    "product": "product_referral",
    "blog": "blog_referral",
}


class RewardService:

    @staticmethod
    def grant_share_reward(env, partner, url, content_name=False, source_id=False,
                            return_reason=False):
        """Grant the instant Share Reward for a Share-button click.

        :param return_reason: when True, returns a tuple
            ``(share_or_False, reason_or_None)`` instead of just the
            record, so a caller that wants to show the user WHY a
            reward wasn't granted (see controllers/share.py) can do so.
            Defaults to False so every existing caller (the
            backward-compatible models/share_record.py wrapper, tests,
            any external code) keeps getting exactly the same
            record-or-False return value as before - this is purely
            additive.
        :return: the created social.share.record, or False if the
            reward could not be granted for any reason (feature
            disabled, no handler, no program, validation failed). When
            `return_reason` is True, a tuple of that value plus a
            reason code (None on success) is returned instead.
        """
        def _result(value, reason):
            return (value, reason) if return_reason else value

        ShareRecord = env["social.share.record"]
        content_type = ShareRecord.classify_content_type(url)

        trigger_code = SHARE_TRIGGER_MAP.get(content_type)

        if not trigger_code:
            # "other" pages (anything not event/shop/blog) are not a
            # supported reward trigger - safely ignored, same as an
            # unregistered handler would be.
            RewardValidationService.log(
                env, "info",
                "Share on unsupported content type '%s' - no reward "
                "trigger exists for it, safely ignored.", content_type,
            )
            return _result(False, "unsupported_content_type")

        try:
            source_res_id = int(source_id) if source_id else False
        except (TypeError, ValueError):
            source_res_id = False

        try:
            with env.cr.savepoint():
                handler, program, points, reason = RewardValidationService.resolve(
                    env, trigger_code, "share", partner=partner,
                )

                if reason:
                    return _result(False, reason)

                share = handler.execute(
                    program,
                    partner=partner,
                    url=url,
                    content_name=content_name,
                    source_res_id=source_res_id,
                    points_override=points,
                    content_type=content_type,
                )
                return _result(share, None if share else "internal_error")
        except Exception:
            # Same guarantee as register_referral() below: a Share
            # Reward must never be able to break the page/request that
            # triggered it. The savepoint confines any unexpected DB
            # error to just this attempt.
            _logger.exception(
                "grant_share_reward() failed unexpectedly for content_type "
                "'%s' - safely ignored.", content_type,
            )
            return _result(False, "internal_error")

    @staticmethod
    def register_referral(env, referral_type, referrer_partner, referred_partner, **extra):
        """Register (and, per the existing auto-claim design, immediately
        credit) a referral reward.

        :param referral_type: 'event' | 'product' | 'blog'
        :param extra: passed straight through to the handler/model, e.g.
            registration_id=, sale_order_id=, product_id=, blog_post_id=
        :return: the social.referral.record (new or pre-existing), or
            False if the reward could not be granted for any reason.
        """
        trigger_code = REFERRAL_TRIGGER_MAP.get(referral_type)
        if not trigger_code:
            RewardValidationService.log(
                env, "warning",
                "register_referral() called with unknown referral_type "
                "'%s' - safely ignored.", referral_type,
            )
            return False

        # Defensive: extra may carry ids sourced from a browser cookie
        # (registration_id / sale_order_id / product_id / blog_post_id).
        # Cookies can outlive the record they point to, or be stale from
        # an earlier/different referral type entirely (e.g. a leftover
        # blog_post_id cookie still present when the current referral is
        # actually an event/product one). Passing a dangling id straight
        # into ReferralRecord.create() would hit a hard FK violation at
        # the database level - drop anything that doesn't actually exist
        # any more so we only ever pass ids that are safe to insert.
        id_model_map = {
            "registration_id": "event.registration",
            "sale_order_id": "sale.order",
            "product_id": "product.product",
            "blog_post_id": "blog.post",
        }
        for key, model_name in id_model_map.items():
            value = extra.get(key)
            if not value:
                continue
            if not env[model_name].sudo().browse(int(value)).exists():
                extra[key] = False

        try:
            with env.cr.savepoint():
                handler, program, points, reason = RewardValidationService.resolve(
                    env, trigger_code, "referral",
                    referrer_partner=referrer_partner,
                    referred_partner=referred_partner,
                    **extra,
                )

                if reason:
                    return False

                return handler.execute(
                    program,
                    referrer_partner=referrer_partner,
                    referred_partner=referred_partner,
                    points_override=points,
                    **extra,
                )
        except Exception:
            # Whatever goes wrong here (unexpected FK/constraint error,
            # a bug in a handler, etc), a referral reward must NEVER be
            # able to take down the caller's own transaction (account
            # signup, order confirmation, registration creation). The
            # savepoint above means this rolls back only the referral
            # attempt itself; the caller's work is untouched.
            _logger.exception(
                "register_referral() failed unexpectedly for referral_type "
                "'%s' - safely ignored, caller's transaction is unaffected.",
                referral_type,
            )
            return False

    @staticmethod
    def grant_signup_reward(env, partner):
        """Grant the one-time, non-shareable Customer Signup reward.

        Unlike grant_share_reward (repeatable) and register_referral
        (repeatable per distinct referred person), this can only ever
        succeed once per partner - see res.partner.signup_reward_granted
        and handlers/customer_signup.py.

        :return: the rewarded res.partner record, or False if the
            reward could not be granted for any reason (feature
            disabled, no handler, no program, already granted,
            validation failed).
        """
        trigger_code = "customer_signup"

        if not partner or not partner.id:
            return False

        try:
            with env.cr.savepoint():
                handler, program, points, reason = RewardValidationService.resolve(
                    env, trigger_code, "signup", partner=partner,
                )

                if reason:
                    return False

                result = handler.execute(
                    program, partner=partner, points_override=points,
                )
                return result
        except Exception:
            # Same guarantee as grant_share_reward()/register_referral()
            # above: a Signup Reward must never be able to break the
            # account-creation flow that triggered it.
            _logger.exception(
                "grant_signup_reward() failed unexpectedly - safely "
                "ignored, caller's transaction is unaffected.",
            )
            return False
