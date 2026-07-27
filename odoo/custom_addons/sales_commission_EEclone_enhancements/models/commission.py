from odoo import api,models, fields
from odoo.exceptions import ValidationError

class SalesCommission(models.Model):

    @api.constrains("target_completion", "commission", "otc")
    def _check_values(self):
        for rec in self:
            if rec.target_completion < 0:
                raise ValidationError("Target Completion cannot be negative.")

            if rec.commission < 0:
                raise ValidationError("Commission Amount cannot be negative.")

            if rec.otc < 0:
                raise ValidationError("OTC % cannot be negative.")
        
    _name = "sales.commission"
    _description = "Commission Level"
    _order = "sequence, target_completion"

    plan_id = fields.Many2one(
        "sales.commission.plan",
        string="Commission Plan",
        required=True,
        ondelete="cascade",
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )

    target_completion = fields.Float(
        string="Target Completion (%)",
        required=True,
    )

    commission = fields.Float(
        string="Commission Amount",
        default=0.0,
    )

    otc = fields.Float(
        string="OTC %",
        default=0.0,
    )

    _sql_constraints = [
        (
            "unique_target_completion",
            "unique(plan_id, target_completion)",
            "Target completion percentage must be unique for a commission plan.",
        ),
    ]