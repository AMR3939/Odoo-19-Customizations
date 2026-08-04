# -*- coding: utf-8 -*-
"""
RewardValidationService centralizes the validation layer described in the
architecture spec:

    Program Active
    Reward Trigger Exists
    Registered Handler Exists
    Reward Configured
    Customer Eligible
    Duplicate Prevention
    Self Referral Prevention

If ANY check fails, no points are ever awarded and the module exits
safely (returns a reason string instead of raising). Rewarding loyalty
points is always a side effect, never a precondition, of the underlying
Odoo flow (event registration, sale confirmation, user signup, share
click) - nothing in this service ever raises to block that flow.
"""

import logging

from ..handlers.registry import get_handler

_logger = logging.getLogger(__name__)

CONFIG_PREFIX = "social_sharing_loyalty_points_enhancement."

#: Maps every internal "reason" string this service (and the handlers'
#: validate()/is_eligible()) can return to a short, user-safe message -
#: never exposes internal states like config parameter names or model
#: internals. Used only by callers that explicitly opt in to surfacing a
#: validation error to the end user (see RewardService.grant_share_reward's
#: `return_reason` argument) - the default/legacy behaviour of silently
#: returning False everywhere else is unchanged.
REASON_MESSAGES = {
    "feature_disabled": "This reward is currently turned off.",
    "no_handler_registered": "This type of reward isn't available yet.",
    "no_program_configured": "No active reward program is set up for this action yet.",
    "reward_not_configured": "This reward program isn't fully configured yet.",
    "program_inactive": "This reward program is currently inactive.",
    "program_trigger_mismatch": "This reward program isn't set up for this action.",
    "no_partner": "You need to be logged in to earn this reward.",
    "partner_inactive": "Your account can't currently earn rewards.",
    "not_eligible": "You're not eligible for this reward right now.",
    "unsupported_content_type": "Rewards aren't available on this page.",
    "internal_error": "Something went wrong - your reward couldn't be processed.",
}

DEFAULT_REASON_MESSAGE = "This reward couldn't be granted right now."

#: Reasons that reflect a store *configuration/setup* problem rather than
#: anything about the visitor or their eligibility - e.g. no admin has
#: configured a loyalty program for this trigger yet, or the feature is
#: turned off in Settings. These are never the shopper's fault and never
#: actionable by them, so they must NOT be surfaced as a toast on the
#: storefront (that just makes the store look broken to customers). They
#: are still logged server-side (see resolve()/log() below) for whoever
#: administers the site. Every reason NOT in this set is considered
#: user-relevant (e.g. "you need to log in", "you already claimed this")
#: and is safe to show.
#:
#: NOTE: "no_handler_registered" is deliberately NOT in this set (as of
#: this revision), even though it is technically a backend/dev gap
#: rather than anything the visitor caused. Product decision: this
#: reason should only ever be reachable via a technical/DB-level
#: misconfiguration (see loyalty_program.py's dynamic selection, which
#: prevents picking an unhandled trigger through the UI), so surfacing
#: it as a visible "This type of reward isn't available yet." message
#: is treated as an acceptable, honest signal rather than something
#: that makes the store look broken - unlike the more common
#: "unsupported_content_type" case (share button clicked on an
#: untracked page), which stays silent because it happens routinely
#: and is not a genuine error.
SILENT_REASONS = {
    "feature_disabled",
    "no_program_configured",
    "reward_not_configured",
    "program_inactive",
    "program_trigger_mismatch",
    "unsupported_content_type",
    "internal_error",
}


class RewardValidationService:

    @staticmethod
    def get_user_message(reason):
        """Translates an internal reason code into a short, user-safe
        message suitable for display in a UI popup/toast. Falls back to
        a generic message for any reason not explicitly mapped above
        (e.g. a handler-specific eligibility reason like
        'already_shared' or 'self_referral_not_allowed') so a new
        handler never needs to touch this file to stay safe.

        Returns None for any reason in SILENT_REASONS (a store
        configuration/setup problem, not something about the visitor) -
        callers must treat None as "don't show anything to the user",
        since these are never the shopper's fault or actionable by
        them. The reason is still logged server-side by resolve().
        """
        if reason in SILENT_REASONS:
            return None
        return REASON_MESSAGES.get(reason, DEFAULT_REASON_MESSAGE)

    # ------------------------------------------------------------------
    # Global settings helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _param_bool(env, key, default="True"):
        ICP = env["ir.config_parameter"].sudo()
        return ICP.get_param(CONFIG_PREFIX + key, default=default) == "True"

    @staticmethod
    def is_logging_enabled(env):
        return RewardValidationService._param_bool(env, "reward_logging_enabled", "True")

    @staticmethod
    def is_registry_validation_enabled(env):
        return RewardValidationService._param_bool(env, "registry_validation_enabled", "True")

    @staticmethod
    def is_feature_enabled(env, feature, trigger_code=None):
        """`feature` is 'share', 'referral', or 'signup'.

        Every family is gated by a PER-TRIGGER switch instead of one
        combined switch each - 'share' split first (product/blog/
        event), 'referral' split the same way afterwards (event/
        product/blog), 'signup' added as its own single-trigger family.
        Every other check below is untouched.
        """
        share_keys = {
            "product_share": "enable_product_share_rewards",
            "blog_share": "enable_blog_share_rewards",
            "event_share": "enable_event_share_rewards",
        }
        referral_keys = {
            "event_referral": "enable_event_referral_rewards",
            "product_referral": "enable_product_referral_rewards",
            "blog_referral": "enable_blog_referral_rewards",
        }
        signup_keys = {
            "customer_signup": "enable_customer_signup_rewards",
        }
        feature_keys = {"share": share_keys, "referral": referral_keys, "signup": signup_keys}
        keys = feature_keys.get(feature, referral_keys)

        key = keys.get(trigger_code)
        if not key:
            # Not one of the known triggers for this feature (e.g. a
            # future custom trigger) - default to enabled rather than
            # silently blocking an unknown case.
            return True
        return RewardValidationService._param_bool(env, key, "True")

    @staticmethod
    def log(env, level, message, *args):
        if not RewardValidationService.is_logging_enabled(env):
            return
        getattr(_logger, level)(message, *args)

    # ------------------------------------------------------------------
    # Program resolution
    # ------------------------------------------------------------------
    @staticmethod
    def find_program_and_points(env, trigger_code):
        """Reward Trigger Exists check.

        Looks for exactly one active loyalty.program configured with
        this reward_trigger. If none exists, falls back to the global
        "Default Loyalty Program" / "Default Reward Points" from
        Settings, but ONLY if the admin explicitly enabled that
        fallback - this lets a brand-new trigger start working
        immediately while a dedicated program is being set up, without
        ever silently guessing at behaviour.

        :return: tuple(loyalty.program recordset (possibly empty), int points)
        """
        Program = env["loyalty.program"].sudo()

        domain = [
            ("reward_trigger", "=", trigger_code),
            ("active", "=", True),
        ]

        program = Program.search(domain, limit=1)

        if program:
            return program, program.reward_trigger_points

        ICP = env["ir.config_parameter"].sudo()

        default_program_id = int(ICP.get_param(CONFIG_PREFIX + "default_loyalty_program_id", "0") or 0)
        default_points = int(ICP.get_param(CONFIG_PREFIX + "default_reward_points", "0") or 0)

        if not default_program_id or default_points <= 0:
            return Program.browse(), 0

        default_program = Program.browse(default_program_id).exists()
        if not default_program or not default_program.active:
            return Program.browse(), 0

        return default_program, default_points

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    @staticmethod
    def resolve(env, trigger_code, feature, **context):
        """Runs the full validation pipeline for `trigger_code`.

        :param feature: 'share' or 'referral' - which master switch to
            check first.
        :return: tuple(handler_or_None, program_or_None, points, reason_or_None)
                 reason is None only when it is now safe to call
                 handler.execute(program, points_override=points, **context)
        """
        if not RewardValidationService.is_feature_enabled(env, feature, trigger_code):
            RewardValidationService.log(
                env, "info",
                "%s rewards are disabled in Settings - reward for trigger "
                "'%s' skipped.", feature.title(), trigger_code,
            )
            return None, None, 0, "feature_disabled"

        handler = get_handler(trigger_code, env)
        if not handler:
            # get_handler() already logs its own warning.
            return None, None, 0, "no_handler_registered"

        program, points = RewardValidationService.find_program_and_points(
            env, trigger_code,
        )
        if not program:
            RewardValidationService.log(
                env, "info",
                "No active Loyalty Program configured for reward trigger "
                "'%s' - reward safely skipped.", trigger_code,
            )
            return handler, None, 0, "no_program_configured"

        is_fallback = program.reward_trigger != trigger_code

        if RewardValidationService.is_registry_validation_enabled(env):
            if is_fallback:
                # A fallback program was not authored for this trigger,
                # so only the trigger-specific eligibility checks apply
                # (duplicate prevention, self-referral, customer
                # eligibility) - not the "program.reward_trigger must
                # match" check, which would always fail for it by
                # definition.
                if not points or points <= 0:
                    return handler, program, 0, "reward_not_configured"
                ok, reason = handler.is_eligible(program, **context)
            else:
                ok, reason = handler.validate(program, **context)
            if not ok:
                if reason in handler.IDEMPOTENT_REASONS:
                    # Not a real failure - this exact reward was already
                    # granted before (e.g. the same referral reported
                    # twice). execute() is required to be idempotent for
                    # these reasons specifically, so let it run: it will
                    # return the pre-existing record instead of creating
                    # a duplicate, rather than the caller getting back a
                    # bare False as if something had gone wrong.
                    RewardValidationService.log(
                        env, "info",
                        "Reward for trigger '%s' already granted (%s) - "
                        "returning existing record, no new points.",
                        trigger_code, reason,
                    )
                    return handler, program, points, None

                RewardValidationService.log(
                    env, "info",
                    "Reward validation failed for trigger '%s': %s",
                    trigger_code, reason,
                )
                return handler, program, points, reason

        return handler, program, points, None