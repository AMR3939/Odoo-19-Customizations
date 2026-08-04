# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    signup_reward_granted = fields.Boolean(
        string="Signup Reward Granted",
        default=False,
        readonly=True,
        help="Technical flag: whether this partner has already received "
             "the one-time Customer Signup reward. Unlike Share/Referral "
             "rewards, a signup reward can only ever be earned once per "
             "customer - this flag is how handlers.customer_signup "
             "enforces that, independent of which loyalty.program is "
             "currently configured for the trigger.",
    )

    referral_record_ids = fields.One2many(
        "social.referral.record",
        "referrer_partner_id",
        string="Referral Rewards",
        readonly=True,
    )

    referral_count = fields.Integer(
        string="Referral Count",
        compute="_compute_referral_count",
    )

    total_referral_points = fields.Integer(
        string="Total Referral Points",
        compute="_compute_total_referral_points",
    )

    def _compute_referral_count(self):
        for partner in self:
            partner.referral_count = len(partner.referral_record_ids)

    def _compute_total_referral_points(self):
        for partner in self:
            partner.total_referral_points = sum(
                partner.referral_record_ids.filtered(
                    lambda r: r.state == "rewarded"
                ).mapped("rewarded_points")
            )