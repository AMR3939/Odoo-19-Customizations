from odoo import models, fields


class SalesCommissionTarget(models.Model):
    _name = "sales.commission.target"
    _description = "Sales Commission Target"
    _order = "date_from"

    plan_id = fields.Many2one(
        "sales.commission.plan",
        string="Commission Plan",
        required=True,
        ondelete="cascade",
    )

    name = fields.Char(
        string="Period",
        required=True,
    )

    date_from = fields.Date(
        string="From",
        required=True,
    )

    date_to = fields.Date(
        string="To",
        required=True,
    )

    target_amount = fields.Float(
        string="Target",
        default=0.0,
    )