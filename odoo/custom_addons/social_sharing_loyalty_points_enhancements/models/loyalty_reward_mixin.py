# -*- coding: utf-8 -*-

from odoo import models


class LoyaltyRewardMixin(models.AbstractModel):
    _name = "social.loyalty.reward.mixin"
    _description = "Shared helper for crediting loyalty point rewards"

    def _credit_loyalty_points(self, partner, program, points, description,
                                order_model=False, order_id=False):
        """
        Add `points` to `partner`'s loyalty.card for `program` (creating the
        card if they don't have one yet), and log a loyalty.history entry
        for it.

        Both social.referral.record (action_claim / share reversal) and
        social.share.record (instant grant) call this so there is exactly
        one place that ever writes to loyalty.card - avoids the two
        systems drifting apart or double-crediting in different ways.

        Returns (card, history) for `program`.
        """
        LoyaltyCard = self.env["loyalty.card"].sudo()
        LoyaltyHistory = self.env["loyalty.history"].sudo()

        card = LoyaltyCard.search(
            [
                ("partner_id", "=", partner.id),
                ("program_id", "=", program.id),
            ],
            limit=1,
        )

        if not card:
            card = LoyaltyCard.create({
                "partner_id": partner.id,
                "program_id": program.id,
                "points": 0,
            })

        card.write({"points": card.points + points})

        history = LoyaltyHistory.create({
            "card_id": card.id,
            "description": description,
            "issued": points,
            "order_model": order_model,
            "order_id": order_id,
        })

        return card, history