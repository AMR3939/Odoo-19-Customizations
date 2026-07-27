from odoo import api, fields, models


class SalesCommissionRecord(models.Model):
    _name = "sales.commission.record"
    _description = "Sales Commission Record"
    _rec_name = "salesperson_id"
    _order = "period desc, salesperson_id"

    # ---------------------------------------------------------
    # Basic Information
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

    target_id = fields.Many2one(
    "sales.commission.target",
    string="Target Period",
    required=True,
    ondelete="cascade",
)

    period = fields.Date(
        related="target_id.date_from",
        string="Period",
        store=True,
        readonly=True,
    )

    target_amount = fields.Float(
        related="target_id.target_amount",
        string="Target Amount",
        store=True,
        readonly=True,
        aggregator="avg",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("paid", "Paid"),
        ],
        string="Status",
        default="draft",
        required=True,
    )

    # ---------------------------------------------------------
    # Commission Details
    # ---------------------------------------------------------

    achieved = fields.Float(
        string="Achieved",
        default=0.0,
    )

    achieved_rate = fields.Float(
        string="Achieved Rate",
        compute="_compute_achieved_rate",
        store=True,
        aggregator="avg",
    )

    commission = fields.Float(
        string="Commission",
        compute="_compute_commission",
        store=True,
    )

    # ---------------------------------------------------------
    # Compute Methods
    # ---------------------------------------------------------

    @api.depends("target_amount", "achieved")
    def _compute_achieved_rate(self):
        for rec in self:
            if rec.target_amount > 0:
                rec.achieved_rate = (
                    rec.achieved / rec.target_amount
                ) * 100
            else:
                rec.achieved_rate = 0.0

    @api.depends(
        "achieved",
        "achieved_rate",
        "target_amount",
        "plan_id.commission_ids.target_completion",
        "plan_id.commission_ids.commission",
        "plan_id.commission_ids.otc",
    )
    def _compute_commission(self):
        """
        Look up the commission owed for this record's achieved rate
        against the plan's tiered Commission Levels table (the same
        levels the Commission Curve graph plots).

        - Below the lowest defined level: no commission yet.
        - Between two levels: commission is interpolated linearly
          along the straight line connecting them (this matches the
          Commission Curve graph exactly).
        - Above the highest defined level: the base commission for
          that level, plus an OTC % bonus applied to whatever amount
          was achieved beyond that level's target threshold.
        """
        for rec in self:
            levels = rec.plan_id.commission_ids.sorted(
                key=lambda level: level.target_completion
            )

            if not levels:
                rec.commission = 0.0
                continue

            rate = rec.achieved_rate
            first_level = levels[0]
            last_level = levels[-1]

            if rate <= first_level.target_completion:
                rec.commission = (
                    first_level.commission
                    if rate >= first_level.target_completion
                    else 0.0
                )
                continue

            if rate >= last_level.target_completion:
                threshold_amount = (
                    last_level.target_completion / 100.0
                ) * rec.target_amount

                extra_amount = max(
                    rec.achieved - threshold_amount, 0.0
                )

                rec.commission = (
                    last_level.commission
                    + extra_amount * (last_level.otc / 100.0)
                )
                continue

            commission_value = last_level.commission

            for lower, upper in zip(levels, levels[1:]):
                if lower.target_completion <= rate <= upper.target_completion:
                    span = upper.target_completion - lower.target_completion

                    if span <= 0:
                        commission_value = upper.commission
                    else:
                        ratio = (
                            rate - lower.target_completion
                        ) / span

                        commission_value = (
                            lower.commission
                            + ratio * (upper.commission - lower.commission)
                        )
                    break

            rec.commission = commission_value

        self._sync_report()
                
    _sql_constraints = [
    (
        "unique_commission_record",
        "unique(plan_id, salesperson_id, target_id)",
        "A commission record already exists for this salesperson and target period.",
    ),
]
    
    # ---------------------------------------------------------
    # Create Override
    # ---------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_report()
        return records


    # ---------------------------------------------------------
    # Write Override
    # ---------------------------------------------------------

    def write(self, vals):
        result = super().write(vals)
        self._sync_report()
        return result
    
    # ---------------------------------------------------------
    # Sync Report
    # ---------------------------------------------------------

    def _sync_report(self):
        Report = self.env["sales.commission.report"]

        for rec in self:

            report = Report.search([
                ("plan_id", "=", rec.plan_id.id),
                ("salesperson_id", "=", rec.salesperson_id.id),
                ("period", "=", rec.period),
            ], limit=1)

            values = {
                "plan_id": rec.plan_id.id,
                "salesperson_id": rec.salesperson_id.id,
                "period": rec.period,
                "target_amount": rec.target_amount,
                "achieved": rec.achieved,
                "achieved_rate": rec.achieved_rate,
                "commission": rec.commission,
                "state": rec.state,
            }

            if report:
                report.write(values)
            else:
                Report.create(values)