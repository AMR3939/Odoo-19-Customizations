from odoo import models, fields


class SalesCommissionAchievement(models.Model):
    _name = "sales.commission.achievement"
    _description = "Commission Achievement"

    plan_id = fields.Many2one(
        "sales.commission.plan",
        string="Commission Plan",
        ondelete="cascade",
        required=True,
    )

    achievement_type = fields.Selection(
        [
            ("amount_invoiced", "Amount Invoiced"),
            ("amount_sold", "Amount Sold"),
            ("quantity", "Quantity Sold"),
        ],
        string="Type",
        default="amount_invoiced",
        required=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
    )

    category_id = fields.Many2one(
        "product.category",
        string="Category",
    )

    rate = fields.Float(
        string="Rate (%)",
        default=5.0,
    )