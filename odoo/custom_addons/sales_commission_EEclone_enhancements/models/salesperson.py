from odoo import models, fields


class SalesCommissionSalesperson(models.Model):
    _name = "sales.commission.salesperson"
    _description = "Commission Salesperson"
    _rec_name = "user_id"

    plan_id = fields.Many2one(
        "sales.commission.plan",
        string="Commission Plan",
        required=True,
        ondelete="cascade",
    )

    user_id = fields.Many2one(
    "res.users",
    string="Salesperson",
    required=True,
    )

    date_from = fields.Date(
        string="From",
    )

    date_to = fields.Date(
        string="To",
    )

    other_plan_count = fields.Integer(
        string="Other Plans",
        default=0,
        readonly=True,
    )