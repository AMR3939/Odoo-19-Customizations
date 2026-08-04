# -*- coding: utf-8 -*-
"""
Shared logic for the three "instant Share Reward" handlers
(product_share, blog_share, event_share).

Each concrete handler only needs to set two class attributes -
`trigger_code` and `content_type` - everything else (eligibility,
crediting the points, logging) lives here exactly once.
"""

from odoo import _

from .base_handler import BaseRewardHandler


class BaseShareHandler(BaseRewardHandler):
    """Common implementation for every "click Share -> get points instantly"
    reward. Subclasses: handlers/product_share.py, handlers/blog_share.py,
    handlers/event_share.py.
    """

    #: 'product' | 'blog' | 'event' - must match social.share.record's
    #: content_type selection.
    content_type = None

    def is_eligible(self, program, partner=None, **context):
        """Customer Eligible check for share rewards: a real, active
        partner must be provided. Whether that partner is a logged-in
        portal user (as opposed to the anonymous public partner) is
        already enforced upstream, in controllers/share.py, before the
        reward service is ever called - kept there rather than here
        because it is a request/session-level concern, not a
        program/points concern.
        """
        if not partner or not partner.id:
            return False, "no_partner"

        if not partner.active:
            return False, "partner_inactive"

        return True, None

    def execute(self, program, partner=None, url=None, content_name=False,
                source_res_id=False, points_override=None, **context):
        ShareRecord = self.env["social.share.record"].sudo()

        # points_override is set by RewardValidationService when the
        # program being used is a global "Default Loyalty Program"
        # fallback rather than one dedicated to this trigger - in that
        # case the program's own reward_trigger_points does not apply.
        points = points_override if points_override is not None else program.reward_trigger_points

        share = ShareRecord.create({
            "sharer_partner_id": partner.id,
            "content_type": self.content_type,
            "content_name": content_name or "",
            "shared_url": url or "",
            "source_res_id": source_res_id or False,
            "loyalty_program_id": program.id,
            "rewarded_points": points,
        })

        # NOTE: content_type is a DYNAMIC Selection (selection=
        # "_get_content_type_selection", see models/share_record.py) so
        # that Page Type Registry rows can appear as valid values too.
        # For a dynamic Selection, `._fields["content_type"].selection`
        # is just the method's NAME (a string), not the resolved list -
        # calling the method directly is what actually returns the
        # list of (value, label) tuples.
        content_type_label = dict(
            ShareRecord._get_content_type_selection()
        ).get(self.content_type, self.content_type.title())

        description = _(
            "Share Reward: %(name)s (%(type)s)",
            name=content_name or url or content_type_label,
            type=content_type_label,
        )

        card, history = share._credit_loyalty_points(
            partner, program, points, description,
        )
        share.loyalty_history_id = history.id

        return share
