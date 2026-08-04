# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ReferralRecord(models.Model):
    _name = "social.referral.record"
    _inherit = ["social.loyalty.reward.mixin"]
    _description = "Social Referral Reward Record"
    _order = "reward_date desc, id desc"
    _rec_name = "referrer_partner_id"

    referrer_partner_id = fields.Many2one(
        "res.partner",
        string="Referrer",
        required=True,
        index=True,
        ondelete="cascade",
    )

    referred_partner_id = fields.Many2one(
        "res.partner",
        string="Referred User",
        required=True,
        index=True,
        ondelete="cascade",
    )

    referral_type = fields.Selection(
        [
            ("event", "Event"),
            ("product", "Product"),
            ("blog", "Blog"),
        ],
        string="Referral Source",
        required=True,
        default="event",
        index=True,
        readonly=True,
        help="What was shared to generate this referral: an Event, a "
             "Product, or a Blog post.",
    )

    # --- Event referrals ----------------------------------------------------
    registration_id = fields.Many2one(
        "event.registration",
        string="Event Registration",
        readonly=True,
        ondelete="cascade",
        help="Set only when referral_type = 'event'.",
    )

    event_id = fields.Many2one(
        "event.event",
        string="Event",
        related="registration_id.event_id",
        store=True,
        readonly=True,
    )

    # --- Product referrals ---------------------------------------------------
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        readonly=True,
        ondelete="set null",
        help="First confirmed order placed by the referred user. Set only "
             "when referral_type = 'product'.",
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product Shared",
        readonly=True,
        ondelete="set null",
        help="Product that was shared and led to this referral. Set only "
             "when referral_type = 'product'.",
    )

    # --- Blog referrals -------------------------------------------------
    blog_post_id = fields.Many2one(
        "blog.post",
        string="Blog Post",
        readonly=True,
        ondelete="set null",
        help="Blog post that was shared and led to this referral. Set "
             "only when referral_type = 'blog'.",
    )

    # --- Common ----------------------------------------------------------------
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

    reward_date = fields.Datetime(
        string="Reward Date",
        default=fields.Datetime.now,
        readonly=True,
    )

    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("rewarded", "Rewarded"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="pending",
        required=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "unique_registration_referral",
            "unique(registration_id)",
            "A referral reward has already been processed for this registration.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """
        Auto-claim referral rewards the moment they become eligible.

        Per product decision, referrers should no longer have to visit a
        dedicated "My Referrals" page and click "Claim Now" - the points
        must already be on their loyalty card (and visible on the
        unified "My Loyalty Points" portal page) as soon as the referral
        is recorded, whether it came from an event registration, a
        product purchase, or a blog signup. Every caller
        (event_registration.py, sale_order.py, res_users.py) still
        creates these rows with state='pending', so this override is the
        single place that immediately grants the points, regardless of
        which flow created the record.
        """
        records = super().create(vals_list)
        records.action_claim()
        return records

    @api.constrains("referral_type", "referrer_partner_id", "referred_partner_id")
    def _check_unique_referral_per_type(self):
        """
        `registration_id` can legitimately be NULL for product/blog
        referrals (a plain SQL unique index would then let duplicates
        through, since NULL never equals NULL in Postgres), so uniqueness
        for those two types is instead enforced here in Python: a given
        referrer / referred-user pair can only be rewarded ONCE per
        referral type (product, blog). Event referrals stay governed by
        the SQL constraint above (one record per registration), since the
        same referred user may legitimately register for several
        different events and each is a separate, legitimate reward.
        """
        for referral in self:
            if referral.referral_type == "event":
                continue
            duplicate = self.search([
                ("id", "!=", referral.id),
                ("referral_type", "=", referral.referral_type),
                ("referrer_partner_id", "=", referral.referrer_partner_id.id),
                ("referred_partner_id", "=", referral.referred_partner_id.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "A %(type)s referral reward has already been recorded "
                    "for this referrer/referred pair.",
                    type=referral.referral_type,
                ))

    def action_claim(self):
        """
        Grant the loyalty points for a pending referral reward.

        Called automatically from create() as soon as a referral becomes
        eligible - there is no manual "Claim Now" step anymore. Works
        identically for event, product, and blog referrals - only the
        points and program differ.
        """
        for referral in self:

            if referral.state != "pending":
                raise UserError(_("This referral reward is not claimable."))

            if not referral.loyalty_program_id:
                raise UserError(
                    _("No loyalty program is configured for this referral.")
                )

            source_name = {
                "event": referral.event_id.display_name,
                "product": referral.product_id.display_name,
                "blog": referral.blog_post_id.display_name,
            }.get(referral.referral_type) or _("Shared Content")

            type_label = dict(
                self._fields["referral_type"].selection
            ).get(referral.referral_type, referral.referral_type.title())

            card, history = referral._credit_loyalty_points(
                referral.referrer_partner_id,
                referral.loyalty_program_id,
                referral.rewarded_points,
                _(
                    "Referral Reward: %(name)s (%(type)s)",
                    name=source_name,
                    type=type_label,
                ),
                order_model="sale.order",
                order_id=referral.sale_order_id.id,
            )

            referral.write({
                "state": "rewarded",
                "reward_date": fields.Datetime.now(),
                "loyalty_history_id": history.id,
            })

            referral._reverse_matching_share_reward(card, source_name, type_label)

        return True

    def _reverse_matching_share_reward(self, card, source_name, type_label):
        """
        A referral converting means the SAME person already got an
        instant "Share Reward" for clicking Share on this exact piece of
        content, before anyone registered/bought/signed up through their
        link (see social.share.record.grant_share_reward()). Per product
        decision, a converted share should only earn the (larger)
        referral reward, not both - so claw back that earlier share
        grant here, once, the moment the referral is claimed.

        Matching is now exact wherever possible: social.share.record stores
        `source_res_id` (the event/product/blog.post id, read straight off
        the page's `data-referral-source-id` attribute at click time - see
        static/src/js/referral_share.js), and this referral record knows
        the same id for whichever content type it is (`event_id.id` /
        `product_id.id` / `blog_post_id.id`). Matching on that id, plus
        sharer and content type, uniquely identifies the right share.

        Fallback: shares recorded before `source_res_id` existed (or from
        a page that didn't expose one) have it empty, so for those only we
        fall back to the older best-effort title comparison - the content
        name compared on its part before the "|" separator (document.title
        is usually "Page Name | Website Name"), case-insensitively. If
        still no match (e.g. Share Rewards was disabled at share time),
        nothing happens.
        """
        self.ensure_one()

        ShareRecord = self.env["social.share.record"].sudo()

        source_res_id = {
            "event": self.event_id.id,
            "product": self.product_id.id,
            "blog": self.blog_post_id.id,
        }.get(self.referral_type) or False

        shares = self.env["social.share.record"]

        if source_res_id:
            # Reverse EVERY unconverted share this person made for this
            # exact piece of content, not just the most recent one -
            # shares are never deduplicated at grant time (each click is
            # its own instant reward), so a referrer can easily have
            # clicked Share on the same content more than once before it
            # converted. All of those instant grants must be clawed back
            # here, or leftover duplicate-share points stay on the card
            # forever even though "a converted share should only earn
            # the referral reward, not both".
            shares = ShareRecord.search(
                [
                    ("sharer_partner_id", "=", self.referrer_partner_id.id),
                    ("content_type", "=", self.referral_type),
                    ("converted_referral_id", "=", False),
                    ("source_res_id", "=", source_res_id),
                ],
                order="share_date desc",
            )

        if not shares:
            # Legacy fallback - only consider shares that never captured a
            # source id at all, so a share that DID capture one but for a
            # different record is never fuzzy-matched by name instead.
            # Same reasoning as above: reverse every matching share, not
            # just the first one found.
            candidates = ShareRecord.search(
                [
                    ("sharer_partner_id", "=", self.referrer_partner_id.id),
                    ("content_type", "=", self.referral_type),
                    ("converted_referral_id", "=", False),
                    ("source_res_id", "=", False),
                ],
                order="share_date desc",
                limit=20,
            )

            target = (source_name or "").strip().lower()

            matched = self.env["social.share.record"]
            for candidate in candidates:
                candidate_name = (candidate.content_name or "").split("|")[0].strip().lower()
                if candidate_name and target and (
                    candidate_name == target
                    or candidate_name in target
                    or target in candidate_name
                ):
                    matched |= candidate
            shares = matched

        if not shares:
            return

        for share in shares:
            self._credit_loyalty_points(
                card.partner_id,
                card.program_id,
                -share.rewarded_points,
                _(
                    "Share Reward reversed: %(name)s (%(type)s) - "
                    "converted into a referral instead",
                    name=source_name,
                    type=type_label,
                ),
                order_model="sale.order",
                order_id=self.sale_order_id.id,
            )

            share.write({"converted_referral_id": self.id})

            _logger.info(
                "Share reward reversed for %s: %s points clawed back "
                "(share converted into referral %s).",
                self.referrer_partner_id.display_name,
                share.rewarded_points,
                self.id,
            )