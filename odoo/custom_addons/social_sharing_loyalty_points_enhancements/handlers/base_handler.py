# -*- coding: utf-8 -*-
"""
Base class for every reward handler.

The Registry / Handler (Strategy) pattern used by this module works like
this:

    loyalty.program.reward_trigger  (e.g. "product_share")
                    |
                    v
        handlers.registry.get_handler(trigger_code)
                    |
                    v
            BaseRewardHandler subclass instance
                    |
            .validate(program, **context)   -> (bool, reason)
            .execute(program, **context)     -> record | False

Every concrete handler lives in its own file, is registered exactly once
(via the @register_handler decorator in registry.py), and inherits from
this class. Nothing outside handlers/ and services/ is allowed to award
loyalty points directly - this keeps "how a reward is earned" fully
decoupled from "whether a reward is currently configured/enabled".
"""

import logging
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)


class BaseRewardHandler(ABC):
    """Abstract base class every concrete reward handler must inherit from.

    Class attributes to override:
        trigger_code (str): must match one of the values in
            models.loyalty_program.REWARD_TRIGGER_SELECTION. This is the
            key the registry uses to look the handler up.
    """

    #: Must be set by every subclass. Used as the registry key.
    trigger_code = None

    #: Reason codes that is_eligible() can return which are NOT actual
    #: validation failures, just a signal that this exact reward was
    #: already granted before. For these (and only these), the
    #: validation pipeline lets execute() run anyway instead of
    #: short-circuiting - execute() is required to be idempotent (see
    #: its docstring below) and will simply return the pre-existing
    #: record rather than double-crediting. Empty by default; override
    #: on a subclass where "already done" is a real, expected outcome
    #: rather than an error (e.g. BaseReferralHandler's
    #: "duplicate_referral").
    IDEMPOTENT_REASONS = frozenset()

    def __init__(self, env):
        self.env = env

    # ------------------------------------------------------------------
    # Hooks every handler MUST implement
    # ------------------------------------------------------------------
    @abstractmethod
    def is_eligible(self, program, **context):
        """Trigger-specific eligibility check (duplicate prevention,
        self-referral prevention, customer eligibility, etc).

        :return: tuple(bool eligible, str|False reason)
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, program, **context):
        """Perform the actual reward crediting.

        Must be idempotent from the caller's point of view: if called
        for an action that was already rewarded, it should return the
        existing record rather than double-crediting. Handlers achieve
        this by checking for an existing record before creating one.

        :return: the created/existing reward record, or False if nothing
            was (or could be) granted.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Shared validation pipeline - do not override, override
    # is_eligible()/execute() instead.
    # ------------------------------------------------------------------
    def validate(self, program, **context):
        """Runs the full validation layer described in the architecture
        spec, in order, stopping at the first failure:

            1. Program Active
            2. Reward Trigger Exists / matches this handler
            3. Reward Configured (points > 0)
            4. Handler-specific eligibility (customer eligible,
               duplicate prevention, self-referral prevention)

        "Registered Handler Exists" is checked one level up, by
        handlers.registry.get_handler() - if it returns None, we never
        even get a handler instance to call validate() on.
        """
        if not program:
            return False, "no_program_configured"

        if not program.active:
            return False, "program_inactive"

        if program.reward_trigger != self.trigger_code:
            return False, "program_trigger_mismatch"

        if not program.reward_trigger_points or program.reward_trigger_points <= 0:
            return False, "reward_not_configured"

        eligible, reason = self.is_eligible(program, **context)
        if not eligible:
            return False, reason or "not_eligible"

        return True, None