from odoo import models, fields


class SalesCommissionReport(models.Model):
    _name = "sales.commission.report"
    _description = "Sales Commission Report"
    _rec_name = "plan_id"

    plan_id = fields.Many2one(
        "sales.commission.plan",
        string="Commission Plan",
    )

    salesperson_id = fields.Many2one(
        "res.users",
        string="Salesperson",
    )

    period = fields.Date(
        string="Period",
    )

    target_amount = fields.Float(
        string="Target Amount",
    )

    achieved = fields.Float(
        string="Achieved",
    )

    achieved_rate = fields.Float(
        string="Achieved Rate",
    )

    commission = fields.Float(
        string="Commission",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("paid", "Paid"),
        ],
        string="Status",
        default="draft",
    )