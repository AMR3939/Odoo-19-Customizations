from odoo import models, fields


class SalesCommissionAchievementLine(models.Model):
    _name = "sales.commission.achievement.line"
    _description = "Commission Achievement Line"
    _order = "id desc"

    # ---------------------------------------------------------
    # Links
    # ---------------------------------------------------------

    salesperson_id = fields.Many2one(
        "res.users",
        string="Sales Person",
        required=True,
        ondelete="cascade",
    )

    plan_id = fields.Many2one(
        "sales.commission.plan",
        string="Commission Plan",
        required=True,
        ondelete="cascade",
    )

    commission_record_id = fields.Many2one(
        "sales.commission.record",
        string="Commission Record",
        ondelete="cascade",
    )

    target_id = fields.Many2one(
        "sales.commission.target",
        string="Target Period",
        ondelete="cascade",
    )

    move_id = fields.Many2one(
        "account.move",
        string="Invoice",
        ondelete="cascade",
    )

    # ---------------------------------------------------------
    # Snapshot values (captured at the moment the invoice posts,
    # so this line always shows what was true at that time even
    # if the underlying record changes later)
    # ---------------------------------------------------------

    period = fields.Char(
        string="Period",
    )

    commission_target = fields.Float(
        string="Commission Target",
    )

    target = fields.Float(
        string="Target",
    )

    achieved_rate = fields.Float(
        string="Achieved Rate",
        aggregator="avg",
    )

    achieved_rate_display = fields.Char(
        string="Achieved Rate",
        compute="_compute_rate_display",
    )

    commission_rate = fields.Float(
        string="Commission Rate",
        aggregator="avg",
    )

    commission_rate_display = fields.Char(
        string="Commission Rate",
        compute="_compute_rate_display",
    )

    achieved = fields.Float(
        string="Achieved",
    )

    source = fields.Char(
        string="Source",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
    )

    @staticmethod
    def _format_rate(value):
        # Round to 2 decimals, then strip trailing zeros/dot so
        # 40.00 -> "40%", 10.01 -> "10.01%", 28.50 -> "28.5%"
        text = ("%.2f" % (value or 0.0)).rstrip("0").rstrip(".")
        if text in ("", "-"):
            text = "0"
        return "%s%%" % text

    def _compute_rate_display(self):
        for line in self:
            line.achieved_rate_display = self._format_rate(line.achieved_rate)
            line.commission_rate_display = self._format_rate(line.commission_rate)