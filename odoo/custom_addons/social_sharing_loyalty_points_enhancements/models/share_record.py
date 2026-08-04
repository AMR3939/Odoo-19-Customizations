# -*- coding: utf-8 -*-

from odoo import api, fields, models

#: The 4 content types this module has always shipped with. Kept as a
#: plain module-level constant (rather than only living inside the
#: selection method below) so other files can still import it if ever
#: needed, same as REWARD_TRIGGER_SELECTION in loyalty_program.py.
BUILTIN_CONTENT_TYPES = [
    ("event", "Event"),
    ("product", "Product"),
    ("blog", "Blog Post"),
    ("other", "Other Page"),
]


class ShareRecord(models.Model):
    _name = "social.share.record"
    _inherit = ["social.loyalty.reward.mixin"]
    _description = "Social Share Reward Record"
    _order = "share_date desc, id desc"
    _rec_name = "sharer_partner_id"

    sharer_partner_id = fields.Many2one(
        "res.partner",
        string="Sharer",
        required=True,
        index=True,
        ondelete="cascade",
    )

    content_type = fields.Selection(
        selection="_get_content_type_selection",
        string="Content Type",
        required=True,
        default="other",
        readonly=True,
    )

    def _get_content_type_selection(self):
        """The 4 built-in content types this module supports."""
        return BUILTIN_CONTENT_TYPES

    content_name = fields.Char(
        string="Page Title",
        readonly=True,
        help="The page title at the moment it was shared, captured "
             "client-side - kept even if the page is later renamed/removed.",
    )

    shared_url = fields.Char(
        string="Shared URL",
        readonly=True,
    )

    source_res_id = fields.Integer(
        string="Shared Record ID",
        readonly=True,
        help="The exact id of the event/product/blog.post record that was "
             "shared (read from the page's data-referral-source-id "
             "attribute at click time). Used to reliably match this share "
             "to a later referral on the SAME piece of content, instead of "
             "comparing page titles as text. May be empty for shares "
             "recorded before this field existed or on pages that don't "
             "expose a source id - those fall back to the older title-based "
             "match in social.referral.record._reverse_matching_share_reward().",
    )

    loyalty_program_id = fields.Many2one(
        "loyalty.program",
        string="Loyalty Program",
        readonly=True,
        ondelete="set null",
    )

    loyalty_history_id = fields.Many2one(
        "loyalty.history",
        string="Loyalty History",
        readonly=True,
        ondelete="set null",
    )

    rewarded_points = fields.Integer(
        string="Rewarded Points",
        readonly=True,
    )

    share_date = fields.Datetime(
        string="Share Date",
        default=fields.Datetime.now,
        readonly=True,
    )

    converted_referral_id = fields.Many2one(
        "social.referral.record",
        string="Converted Into Referral",
        readonly=True,
        ondelete="set null",
        help="Set once this share later results in an actual referral "
             "(someone registered/bought/signed up through the link). "
             "When that happens the instant share-click points below are "
             "clawed back so the sharer is only credited the (larger) "
             "referral reward instead of both.",
    )

    @api.model
    def classify_content_type(self, url):
        """
        Best-effort classification of a shared URL into a content type,
        based on the path. Checks the 3 built-in prefixes (kept as
        plain if/elif - stable, needs no DB lookup); anything else is
        classified as "other".
        """
        if not url:
            return "other"

        try:
            from urllib.parse import urlparse
            path = urlparse(url).path or ""
        except Exception:
            path = url

        path = path.lower()

        if path.startswith("/event"):
            return "event"
        if path.startswith("/shop"):
            return "product"
        if path.startswith("/blog"):
            return "blog"

        return "other"

    def grant_share_reward(self, partner, url, content_name=False, source_id=False):
        """
        Thin backward-compatible entry point kept for any external code
        (or older JS) that still calls
        `env["social.share.record"].grant_share_reward(...)` directly.

        ALL of the actual logic - which reward_trigger this content type
        maps to, finding the matching active Loyalty Program, running
        the validation layer, and creating the record - now lives in
        services/reward_service.py + handlers/, so there is exactly one
        implementation of "grant a share reward", used by both this
        method and controllers/share.py.

        Returns the created social.share.record, or False if the reward
        could not be granted (feature disabled, no handler registered
        for this content type, no matching Loyalty Program configured,
        or validation failed).
        """
        from ..services.reward_service import RewardService
        return RewardService.grant_share_reward(
            self.env, partner, url,
            content_name=content_name,
            source_id=source_id,
        )