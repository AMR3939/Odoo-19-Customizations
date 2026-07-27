from odoo import models, fields


class SalesCommissionPeriod(models.Model):
    _name = "sales.commission.period"
    _description = "Commission Period"

    name = fields.Char(required=True)

    plan_id = fields.Many2one(
        "sales.commission.plan",
        ondelete="cascade",
        required=True,
    )

    date_from = fields.Date()

    date_to = fields.Date()

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
    )