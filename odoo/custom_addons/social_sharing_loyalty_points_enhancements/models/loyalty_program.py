# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

#: Every reward trigger this module ships a handler for out of the box.
#: To add a new one: add it here, add the matching value to
#: handlers/registry.py (via a new handler module), and nothing else in
#: this model needs to change (Open/Closed Principle).
REWARD_TRIGGER_SELECTION = [
    ("none", "Standard Odoo (No Automatic Reward)"),
    ("product_share", "Product Share"),
    ("blog_share", "Blog Share"),
    ("event_share", "Event Share"),
    ("event_referral", "Event Referral"),
    ("product_referral", "Product Referral"),
    ("blog_referral", "Blog Referral"),
    ("customer_signup", "Customer Signup"),
]


class LoyaltyProgram(models.Model):
    """Extends loyalty.program with a single Reward Trigger selection.

    Previously this module used four independent boolean flags
    (is_social_share_program / is_social_share_reward_program, each with
    their own points field) to decide which programs fed which reward
    flow. That does not scale: every NEW reward type would have meant
    another pair of boolean+integer fields on this model, plus another
    hardcoded if/elif branch wherever points get granted.

    Instead, a Loyalty Program now picks exactly ONE Reward Trigger from
    `reward_trigger`. That trigger is looked up in
    handlers.registry.HANDLER_REGISTRY (see handlers/registry.py) to find
    the Python class responsible for it. If a trigger is selected here
    that has no registered handler (e.g. a reward type was planned but
    its handler module hasn't been added/installed yet), the module
    NEVER crashes and NEVER awards points for it - see
    services/validation_service.py.
    """
    _inherit = "loyalty.program"

    #: Maps a reward_trigger code to the ir.config_parameter key (see
    #: models/social_loyalty_config.py) that must be True for that
    #: trigger to be offered as a pickable option below.
    _TRIGGER_MASTER_SWITCH_MAP = {
        "product_share": "enable_product_share_rewards",
        "blog_share": "enable_blog_share_rewards",
        "event_share": "enable_event_share_rewards",
        "event_referral": "enable_event_referral_rewards",
        "product_referral": "enable_product_referral_rewards",
        "blog_referral": "enable_blog_referral_rewards",
        "customer_signup": "enable_customer_signup_rewards",
    }

    def _get_reward_trigger_selection(self):
        """Dynamic selection for `reward_trigger`: only offers a trigger
        as a pickable option if its master switch (Configuration >
        Social Sharing, Referral & Loyalty Points) is currently on.

        A program that was already assigned a trigger BEFORE its switch
        got turned off keeps its existing value available too - this
        never silently blanks out or invalidates an already-saved
        program, it only stops that trigger being offered to NEW
        selections going forward.
        """
        CONFIG_PREFIX = "social_sharing_loyalty_points_enhancement."
        ICP = self.env["ir.config_parameter"].sudo()

        def is_enabled(switch_key):
            return ICP.get_param(CONFIG_PREFIX + switch_key, default="True") == "True"

        # Keep whatever is already saved on the record(s) currently being
        # rendered selectable, even if its switch has since been turned
        # off - self may be an empty/new recordset, in which case this
        # is simply empty.
        already_selected = set(self.mapped("reward_trigger")) if self else set()

        selection = []
        for code, label in REWARD_TRIGGER_SELECTION:
            if code == "none":
                selection.append((code, label))
                continue
            switch_key = self._TRIGGER_MASTER_SWITCH_MAP.get(code)
            if code in already_selected or not switch_key or is_enabled(switch_key):
                selection.append((code, label))
        return selection

    reward_trigger = fields.Selection(
        selection="_get_reward_trigger_selection",
        string="Reward Trigger",
        default="none",
        help="Which social-sharing/referral action automatically grants "
             "loyalty points on this program. Only one active program "
             "may be assigned to a given trigger at a time. Leave as "
             "'Standard Odoo' for a program that should behave exactly "
             "like a normal, unmodified Loyalty Program (no automatic "
             "crediting by this module at all). Triggers whose master "
             "switch is off in Configuration > Social Sharing, Referral "
             "& Loyalty Points are not offered here - enable the switch "
             "first if you want to assign that trigger to a program.",
    )

    reward_trigger_points = fields.Integer(
        string="Points per Action",
        default=10,
        help="Number of loyalty points credited each time the selected "
             "Reward Trigger fires (once per share click, or once per "
             "successful referral, depending on the trigger).",
    )

    reward_trigger_handler_available = fields.Boolean(
        string="Handler Available",
        compute="_compute_reward_trigger_handler_available",
        help="Technical indicator: whether a reward handler is currently "
             "registered for the selected trigger. If unchecked, this "
             "program's trigger is safely ignored everywhere - no "
             "points will ever be granted through it until a matching "
             "handler is installed.",
    )

    reward_trigger_name_hint = fields.Char(
        string="Reward Trigger Name Hint",
        compute="_compute_reward_trigger_name_hint",
        help="Non-blocking reminder shown when the Program Name doesn't "
             "seem to mention the selected Reward Trigger at all - a "
             "common way triggers end up misconfigured (e.g. a program "
             "named 'Blog Share Reward' actually set to the 'Blog "
             "Referral' trigger). Purely advisory - never prevents "
             "saving.",
    )

    @api.depends("reward_trigger")
    def _compute_reward_trigger_handler_available(self):
        # Imported lazily to avoid any import-order issues between
        # models/ and handlers/ at module load time.
        from ..handlers.registry import get_supported_triggers
        supported = set(get_supported_triggers())
        for program in self:
            program.reward_trigger_handler_available = (
                program.reward_trigger in supported
                if program.reward_trigger and program.reward_trigger != "none"
                else True
            )

    @api.depends("name", "reward_trigger")
    def _compute_reward_trigger_name_hint(self):
        #: Words insignificant enough that their presence alone shouldn't
        #: count as a "match" against a trigger label.
        STOPWORDS = {"share", "referral"}

        for program in self:
            trigger = program.reward_trigger
            if (
                not trigger
                or trigger == "none"
                or not program.name
            ):
                program.reward_trigger_name_hint = False
                continue

            label = dict(REWARD_TRIGGER_SELECTION).get(trigger, "")
            keywords = [
                word.lower() for word in label.split()
                if word.lower() not in STOPWORDS
            ]
            name_lower = program.name.lower()

            if keywords and not any(word in name_lower for word in keywords):
                program.reward_trigger_name_hint = _(
                    "This program's name doesn't mention '%(label)s' - "
                    "just checking you picked the Reward Trigger you "
                    "meant to.",
                    label=label,
                )
            else:
                program.reward_trigger_name_hint = False

    @api.onchange("reward_trigger")
    def _onchange_reward_trigger_suggest_name(self):
        """Fills in a sensible default Program Name the moment a Reward
        Trigger is picked, but ONLY while the name is still empty - never
        overwrites something the user already typed. This removes the
        most common way a program ends up misconfigured: picking a
        trigger first (or last) and forgetting the name doesn't match it.
        """
        if (
            self.reward_trigger
            and self.reward_trigger != "none"
            and not self.name
        ):
            label = dict(REWARD_TRIGGER_SELECTION).get(self.reward_trigger)
            if label:
                self.name = _("%(label)s Reward", label=label)

    #: Points credited by a social-sharing/referral trigger are never
    #: linked to a sale order (see handlers/share_base.py and
    #: handlers/referral_base.py - order_model/order_id are left False
    #: for these), so `applies_on = 'current'` has nothing to anchor to:
    #: the points would be credited but never redeemable. Only
    #: 'future' / 'both' make sense for a socially-triggered program.
    _APPLIES_ON_BROKEN_FOR_SOCIAL_TRIGGER = "current"
    _APPLIES_ON_SAFE_DEFAULT_FOR_SOCIAL_TRIGGER = "future"

    @api.onchange("reward_trigger", "applies_on")
    def _onchange_social_trigger_applies_on(self):
        """Auto-corrects (rather than only warns about) the one
        'Use points on' setting that is structurally incompatible with a
        social-sharing/referral Reward Trigger: 'Current order'. Fires
        whichever of the two fields was changed - picking a social
        trigger while 'Current order' is already set, or switching to
        'Current order' while a social trigger is already set.

        This still leaves the belt-and-braces `@api.constrains` below in
        place for writes that bypass the UI (imports, XML-RPC, scripts).
        """
        if (
            self.reward_trigger
            and self.reward_trigger != "none"
            and self.applies_on == self._APPLIES_ON_BROKEN_FOR_SOCIAL_TRIGGER
        ):
            self.applies_on = self._APPLIES_ON_SAFE_DEFAULT_FOR_SOCIAL_TRIGGER
            return {
                "warning": {
                    "title": _("Use points on: switched to 'Future orders'"),
                    "message": _(
                        "'%(trigger)s' points aren't earned on a sale "
                        "order, so 'Current order' has nothing to apply "
                        "them to and they would never become "
                        "redeemable. This program has been switched to "
                        "'Future orders' instead.",
                        trigger=dict(REWARD_TRIGGER_SELECTION).get(
                            self.reward_trigger, self.reward_trigger
                        ),
                    ),
                }
            }

    @api.constrains("reward_trigger", "applies_on")
    def _check_social_trigger_applies_on(self):
        """Server-side safety net for `_onchange_social_trigger_applies_on`
        above. The onchange only fires from the UI form; this also
        catches writes that skip it entirely (imports, XML-RPC, ORM
        scripts, data migrations) - those must not be allowed to save a
        program in the broken combination, since points earned through
        it would be credited but never redeemable.
        """
        for program in self:
            if (
                program.reward_trigger
                and program.reward_trigger != "none"
                and program.applies_on == self._APPLIES_ON_BROKEN_FOR_SOCIAL_TRIGGER
            ):
                trigger_label = dict(REWARD_TRIGGER_SELECTION).get(
                    program.reward_trigger, program.reward_trigger
                )
                raise ValidationError(_(
                    "'%(name)s' can't use 'Current order' together with "
                    "the '%(trigger)s' Reward Trigger. Social-sharing "
                    "and referral points aren't earned on a sale order, "
                    "so they would never become redeemable. Set 'Use "
                    "points on' to 'Future orders' or 'Current & Future "
                    "orders' instead.",
                    name=program.name,
                    trigger=trigger_label,
                ))

    @api.constrains("reward_trigger", "reward_trigger_points")
    def _check_reward_trigger_points_positive(self):
        """Zero or negative points on an active trigger is not a valid
        real-world configuration - it either silently grants nothing
        (0) or is nonsensical (negative), and previously only surfaced
        as a quiet 'reward_not_configured' skip at grant-time (see
        handlers/base_handler.py) instead of being caught on save. Block
        it here instead, at the same point 'required' already applies
        in the view, so the mistake is caught immediately in the UI.
        """
        for program in self:
            if (
                program.reward_trigger
                and program.reward_trigger != "none"
                and program.reward_trigger_points < 1
            ):
                raise ValidationError(_(
                    "'Points per Action' for '%(name)s' must be at least "
                    "1. A Reward Trigger cannot be saved with 0 or "
                    "negative points - it would never actually grant a "
                    "reward.",
                    name=program.name,
                ))

    @api.constrains("reward_trigger", "active")
    def _check_unique_active_reward_trigger(self):
        """Guard against ambiguous configuration: only one active program
        should be usable per Reward Trigger at a time, otherwise the
        module would not know which card to credit. ('none' is exempt -
        any number of plain/standard programs may exist.)
        """
        for program in self:
            if not program.reward_trigger or program.reward_trigger == "none":
                continue
            if not program.active:
                continue

            domain = [
                ("id", "!=", program.id),
                ("reward_trigger", "=", program.reward_trigger),
                ("active", "=", True),
            ]

            other = self.search(domain, limit=1)
            if other:
                trigger_label = dict(REWARD_TRIGGER_SELECTION).get(
                    program.reward_trigger, program.reward_trigger
                )
                raise ValidationError(_(
                    "Only one active Loyalty Program can be assigned to "
                    "the '%(trigger)s' Reward Trigger at a time. Program "
                    "'%(other)s' is already configured for this.",
                    trigger=trigger_label,
                    other=other.name,
                ))
