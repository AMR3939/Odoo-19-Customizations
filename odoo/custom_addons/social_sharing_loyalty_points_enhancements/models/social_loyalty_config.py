# -*- coding: utf-8 -*-
"""
social.loyalty.config - dedicated, standalone configuration screen for
this module.

Version 2.0 (first release) placed this configuration inside Sales ->
Configuration -> Settings, inheriting sale.res_config_settings_view_form
via XPath. That caused installation/compatibility issues on some Odoo 19
builds and mixed this module's configuration into the generic Settings
screen instead of giving it its own place. This version replaces that
entirely with:

    Sales -> Configuration -> Social Media & Loyalty
                                  -> Social Sharing, Referral & Loyalty Points

a single dedicated menu opening a SINGLETON record of this model - a
regular (non-transient) model with exactly one row, enforced by
get_singleton() below, edited directly (no res.config.settings, no
config_parameter field attribute, no Settings-screen XPath at all).

IMPORTANT - what this file deliberately does NOT do: it does not change
where the configuration is actually STORED. Every field here is a
non-stored compute+inverse pair that reads/writes the exact same
ir.config_parameter keys the reward engine (services/validation_service.py,
models/event_registration.py, models/res_users.py, models/sale_order.py,
models/ir_http.py) already reads directly. That is what makes this a
pure UI/configuration-architecture change: the Registry, the Handlers,
the Validation Layer, and every existing reward flow keep reading
configuration exactly as before and require no changes to function.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

CONFIG_PREFIX = "social_sharing_loyalty_points_enhancement."


class SocialLoyaltyConfig(models.Model):
    _name = "social.loyalty.config"
    _description = "Social Sharing, Referral & Loyalty Points Configuration"

    name = fields.Char(
        default=lambda self: _("Social Sharing, Referral & Loyalty Points"),
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Social Sharing
    # ------------------------------------------------------------------
    enable_product_share_rewards = fields.Boolean(
        string="Enable Product Share Rewards",
        compute="_compute_config", inverse="_inverse_enable_product_share_rewards",
        help="Master switch for the instant 'Product Share' reward trigger. "
             "When off, sharing a product page never grants points, "
             "regardless of Loyalty Program configuration.",
    )

    enable_blog_share_rewards = fields.Boolean(
        string="Enable Blog Share Rewards",
        compute="_compute_config", inverse="_inverse_enable_blog_share_rewards",
        help="Master switch for the instant 'Blog Share' reward trigger.",
    )

    enable_event_share_rewards = fields.Boolean(
        string="Enable Event Share Rewards",
        compute="_compute_config", inverse="_inverse_enable_event_share_rewards",
        help="Master switch for the instant 'Event Share' reward trigger.",
    )

    # ------------------------------------------------------------------
    # Referral
    # ------------------------------------------------------------------
    enable_event_referral_rewards = fields.Boolean(
        string="Enable Event Referral Rewards",
        compute="_compute_config", inverse="_inverse_enable_event_referral_rewards",
        help="Master switch for rewarding a referrer when someone they "
             "referred completes an Event registration. When off, no "
             "event referral is ever rewarded, regardless of Loyalty "
             "Program configuration.",
    )

    enable_product_referral_rewards = fields.Boolean(
        string="Enable Product Referral Rewards",
        compute="_compute_config", inverse="_inverse_enable_product_referral_rewards",
        help="Master switch for rewarding a referrer when someone they "
             "referred completes a plain product purchase (no event "
             "ticket involved).",
    )

    enable_blog_referral_rewards = fields.Boolean(
        string="Enable Blog Referral Rewards",
        compute="_compute_config", inverse="_inverse_enable_blog_referral_rewards",
        help="Master switch for rewarding a referrer when someone they "
             "referred creates a website account after following a "
             "shared blog link.",
    )

    referral_cookie_days = fields.Integer(
        string="Referral Cookie Duration (Days)",
        compute="_compute_config", inverse="_inverse_referral_cookie_days",
        help="Number of days a referral tracking cookie remains valid "
             "after someone clicks a shared link. Shared across all "
             "three referral types above.",
    )

    # ------------------------------------------------------------------
    # Customer Signup
    # ------------------------------------------------------------------
    enable_customer_signup_rewards = fields.Boolean(
        string="Enable Customer Signup Rewards",
        compute="_compute_config", inverse="_inverse_enable_customer_signup_rewards",
        help="Master switch for the one-time 'Customer Signup' reward "
             "trigger. When on, a customer is credited a flat, "
             "non-shareable welcome bonus the moment they create a "
             "website account - once per customer, ever, regardless of "
             "how many times they sign in afterwards. Unlike every "
             "other trigger in this module, this reward has no share "
             "or referral component at all: it cannot be earned by, "
             "attributed to, or passed on to anyone else.",
    )

    # ------------------------------------------------------------------
    # Loyalty
    # ------------------------------------------------------------------
    fallback_loyalty_program_id = fields.Many2one(
        "loyalty.program",
        string="Fallback Loyalty Program",
        domain=[("program_type", "=", "loyalty")],
        compute="_compute_config", inverse="_inverse_fallback_loyalty_program_id",
        help="Used only when a reward trigger has a registered handler "
             "but no dedicated active Loyalty Program of its own yet. "
             "Leave empty to require every trigger to have its own "
             "dedicated program (recommended in production).",
    )

    fallback_reward_points = fields.Integer(
        string="Fallback Reward Points",
        compute="_compute_config", inverse="_inverse_fallback_reward_points",
        help="Points granted through the Fallback Loyalty Program above, "
             "when it applies.",
    )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    registry_validation_enabled = fields.Boolean(
        string="Enable Registry Validation",
        compute="_compute_config", inverse="_inverse_registry_validation_enabled",
        help="Runs the full validation layer (program active, reward "
             "configured, customer eligible, duplicate prevention, "
             "self-referral prevention) before every reward. Keep ON in "
             "production - the Registered Handler Exists check can "
             "never be disabled regardless of this setting, since an "
             "unsupported trigger must always be safely ignored.",
    )

    reward_logging_enabled = fields.Boolean(
        string="Enable Logging",
        compute="_compute_config", inverse="_inverse_reward_logging_enabled",
        help="Log every reward granted, skipped, or rejected by the "
             "validation layer to the Odoo server log.",
    )

    # ------------------------------------------------------------------
    # Reward Trigger Status (read-only diagnostics)
    # ------------------------------------------------------------------
    reward_trigger_status_html = fields.Html(
        string="Reward Trigger Status",
        compute="_compute_reward_trigger_status_html",
        sanitize=False,
    )

    # ==================================================================
    # ir.config_parameter <-> field plumbing
    #
    # Deliberately reuses the exact key names already read by
    # services/validation_service.py and models/*.py, so those files
    # need no changes at all - see module docstring above.
    # ==================================================================
    def _get_param(self, key, default):
        return self.env["ir.config_parameter"].sudo().get_param(CONFIG_PREFIX + key, default=default)

    def _set_param(self, key, value):
        self.env["ir.config_parameter"].sudo().set_param(CONFIG_PREFIX + key, value)

    @api.depends()
    def _compute_config(self):
        ICP = self.env["ir.config_parameter"].sudo()

        def get_bool(key, default="True"):
            return ICP.get_param(CONFIG_PREFIX + key, default=default) == "True"

        product_share = get_bool("enable_product_share_rewards")
        blog_share = get_bool("enable_blog_share_rewards")
        event_share = get_bool("enable_event_share_rewards")
        event_referral = get_bool("enable_event_referral_rewards")
        product_referral = get_bool("enable_product_referral_rewards")
        blog_referral = get_bool("enable_blog_referral_rewards")
        customer_signup = get_bool("enable_customer_signup_rewards")
        cookie_days = int(ICP.get_param(CONFIG_PREFIX + "referral_cookie_days", default="30") or 30)
        fallback_program_id = int(ICP.get_param(CONFIG_PREFIX + "default_loyalty_program_id", default="0") or 0)
        # A Many2one field must be assigned False (never a bare int 0) when
        # there is no value - assigning 0 makes the web client treat it as
        # an unresolved virtual record id and crash in web_read(). Also
        # guard against a stale id (program deleted after being set here).
        Program = self.env["loyalty.program"].sudo()
        fallback_program = (
            Program.browse(fallback_program_id).exists()
            if fallback_program_id else Program.browse()
        )
        fallback_points = int(ICP.get_param(CONFIG_PREFIX + "default_reward_points", default="0") or 0)
        registry_validation = get_bool("registry_validation_enabled")
        logging_enabled = get_bool("reward_logging_enabled")

        for record in self:
            record.enable_product_share_rewards = product_share
            record.enable_blog_share_rewards = blog_share
            record.enable_event_share_rewards = event_share
            record.enable_event_referral_rewards = event_referral
            record.enable_product_referral_rewards = product_referral
            record.enable_blog_referral_rewards = blog_referral
            record.enable_customer_signup_rewards = customer_signup
            record.referral_cookie_days = cookie_days
            record.fallback_loyalty_program_id = fallback_program
            record.fallback_reward_points = fallback_points
            record.registry_validation_enabled = registry_validation
            record.reward_logging_enabled = logging_enabled

    def _inverse_enable_product_share_rewards(self):
        for record in self:
            record._set_param("enable_product_share_rewards", str(record.enable_product_share_rewards))

    def _inverse_enable_blog_share_rewards(self):
        for record in self:
            record._set_param("enable_blog_share_rewards", str(record.enable_blog_share_rewards))

    def _inverse_enable_event_share_rewards(self):
        for record in self:
            record._set_param("enable_event_share_rewards", str(record.enable_event_share_rewards))

    def _inverse_enable_event_referral_rewards(self):
        for record in self:
            record._set_param("enable_event_referral_rewards", str(record.enable_event_referral_rewards))

    def _inverse_enable_product_referral_rewards(self):
        for record in self:
            record._set_param("enable_product_referral_rewards", str(record.enable_product_referral_rewards))

    def _inverse_enable_blog_referral_rewards(self):
        for record in self:
            record._set_param("enable_blog_referral_rewards", str(record.enable_blog_referral_rewards))

    def _inverse_enable_customer_signup_rewards(self):
        for record in self:
            record._set_param("enable_customer_signup_rewards", str(record.enable_customer_signup_rewards))

    def _inverse_referral_cookie_days(self):
        for record in self:
            record._set_param("referral_cookie_days", str(record.referral_cookie_days or 30))

    def _inverse_fallback_loyalty_program_id(self):
        for record in self:
            record._set_param(
                "default_loyalty_program_id",
                str(record.fallback_loyalty_program_id.id or 0),
            )

    def _inverse_fallback_reward_points(self):
        for record in self:
            record._set_param("default_reward_points", str(record.fallback_reward_points or 0))

    def _inverse_registry_validation_enabled(self):
        for record in self:
            record._set_param("registry_validation_enabled", str(record.registry_validation_enabled))

    def _inverse_reward_logging_enabled(self):
        for record in self:
            record._set_param("reward_logging_enabled", str(record.reward_logging_enabled))

    # ------------------------------------------------------------------
    @api.depends()
    def _compute_reward_trigger_status_html(self):
        from ..handlers.registry import get_supported_triggers
        from .loyalty_program import REWARD_TRIGGER_SELECTION

        Program = self.env["loyalty.program"].sudo()
        supported = set(get_supported_triggers())

        rows = []
        for code, label in REWARD_TRIGGER_SELECTION:
            if code == "none":
                continue
            has_handler = code in supported
            program = Program.search([
                ("reward_trigger", "=", code),
                ("active", "=", True),
            ], limit=1)
            handler_icon = "\u2705" if has_handler else "\u26a0\ufe0f"
            program_text = program.name if program else _("Not configured")
            rows.append(
                "<tr>"
                "<td style='padding:2px 12px 2px 0'><b>%s</b></td>"
                "<td style='padding:2px 12px 2px 0'>%s Handler</td>"
                "<td style='padding:2px 0'>%s</td>"
                "</tr>" % (label, handler_icon, program_text)
            )

        table = (
            "<table style='font-size:12px'>"
            "<tr><th style='text-align:left;padding-right:12px'>Reward Trigger</th>"
            "<th style='text-align:left;padding-right:12px'>Registered Handler</th>"
            "<th style='text-align:left'>Active Loyalty Program</th></tr>"
            + "".join(rows) +
            "</table>"
        )

        for record in self:
            record.reward_trigger_status_html = table

    # ==================================================================
    # Singleton enforcement
    # ==================================================================
    @api.model
    def get_singleton(self):
        """Returns the single configuration record, creating it on
        first access if it does not exist yet (e.g. a database that
        upgraded before data/social_loyalty_config_data.xml ran).
        """
        record = self.sudo().search([], limit=1)
        if not record:
            record = self.sudo().create({})
        return record

    @api.model_create_multi
    def create(self, vals_list):
        """Guards against ever ending up with a second row: only the
        very first record (created by data/social_loyalty_config_data.xml
        or by get_singleton() above) is ever allowed to exist.
        """
        if self.sudo().search_count([]) > 0:
            return self.sudo().search([], limit=1)
        return super().create(vals_list)

    def unlink(self):
        raise UserError(_(
            "The Social Sharing, Referral & Loyalty Points configuration "
            "record cannot be deleted."
        ))
