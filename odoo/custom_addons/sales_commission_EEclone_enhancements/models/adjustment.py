from odoo import models, fields


class SalesCommissionAdjustment(models.Model):
    _name = "sales.commission.adjustment"
    _description = "Sales Commission Adjustment"
    _order = "adjustment_date desc"

    # ----------------------------------------------------
    # Relations
    # ----------------------------------------------------

    plan_id = fields.Many2one(
        "sales.commission.plan",
        string="Reduce From",
        required=True,
        ondelete="cascade",
    )

    salesperson_id = fields.Many2one(
        "res.users",
        string="Add to",
        required=True,
    )

    # ----------------------------------------------------
    # Adjustment Details
    # ----------------------------------------------------

    adjustment_date = fields.Date(
        string="Date",
        default=fields.Date.today,
        required=True,
    )

    amount = fields.Float(
        string="Achieved",
        required=True,
    )

    reason = fields.Text(
        string="Note",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
        ],
        string="Status",
        default="draft",
    )