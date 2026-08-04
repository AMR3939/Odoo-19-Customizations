# -*- coding: utf-8 -*-
"""
Central Registry for reward handlers (Registry / Strategy pattern).

This is the ONLY place that maps a `reward_trigger` code to the Python
class responsible for it. To add a brand-new reward type in the future
(Instagram Share, Customer Signup, VIP Campaign, ...):

    1. Add the new code to REWARD_TRIGGER_SELECTION in models/loyalty_program.py
    2. Create handlers/<new_trigger>.py defining a BaseRewardHandler subclass
    3. Decorate it with @register_handler
    4. Import the new module from handlers/__init__.py

No existing handler, service, model, or view needs to change - this is
the Open/Closed Principle in action.

If a Loyalty Program is configured with a reward_trigger that has no
matching entry here (e.g. the module defining its handler was
uninstalled, or an admin picked a trigger that isn't implemented yet),
get_handler() returns None and the caller MUST treat that as "safely do
nothing" - never crash, never guess, never award points.
"""

import logging

_logger = logging.getLogger(__name__)

#: trigger_code (str) -> handler class (type, subclass of BaseRewardHandler)
HANDLER_REGISTRY = {}


def register_handler(handler_cls):
    """Class decorator. Registers `handler_cls` under its `trigger_code`.

    Raises ValueError at import time (i.e. at server start, not at
    runtime) if a handler forgets to set trigger_code, or if two
    handlers ever try to register the same code - both are programming
    errors that should never reach production silently.
    """
    trigger_code = getattr(handler_cls, "trigger_code", None)

    if not trigger_code:
        raise ValueError(
            "Reward handler %r must define a non-empty 'trigger_code' "
            "class attribute before it can be registered." % (handler_cls,)
        )

    if trigger_code in HANDLER_REGISTRY and HANDLER_REGISTRY[trigger_code] is not handler_cls:
        raise ValueError(
            "Reward trigger '%s' is already registered to %r - cannot "
            "also register %r. Each trigger_code must map to exactly "
            "one handler." % (trigger_code, HANDLER_REGISTRY[trigger_code], handler_cls)
        )

    HANDLER_REGISTRY[trigger_code] = handler_cls
    return handler_cls


def get_handler(trigger_code, env):
    """Look up and instantiate the handler for `trigger_code`.

    :param trigger_code: value of loyalty.program.reward_trigger
    :param env: an Odoo Environment, passed through to the handler
    :return: BaseRewardHandler instance, or None if unsupported.
    """
    if not trigger_code or trigger_code == "none":
        return None

    handler_cls = HANDLER_REGISTRY.get(trigger_code)

    if not handler_cls:
        _logger.warning(
            "No reward handler registered for trigger '%s' - unsupported "
            "reward types are always safely ignored, no points are ever "
            "awarded for them.",
            trigger_code,
        )
        return None

    return handler_cls(env)


def get_supported_triggers():
    """Returns the sorted list of trigger codes that currently have a
    registered handler. Used by the Settings screen to show admins which
    Reward Triggers are actually implemented and safe to select."""
    return sorted(HANDLER_REGISTRY.keys())
