from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
import logging

_logger = logging.getLogger(__name__)

class SalesCommissionPlan(models.Model):
    _name = "sales.commission.plan"
    _description = "Sales Commission Plan"

    # ----------------------------------------------------
    # Basic Information
    # ----------------------------------------------------

    name = fields.Char(
        string="Commission Plan",
        required=True
    )

    commission_type = fields.Selection(
        [
            ("achievement", "Achievements"),
            ("target", "Targets"),
        ],
        string="Based On",
        default="achievement",
        required=True,
    )

    applies_on = fields.Selection(
        [
            ("salesperson", "Salesperson"),
            ("sales_team", "Sales Team"),
        ],
        string="Per",
        default="salesperson",
        required=True,
    )

    periodicity = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("yearly", "Yearly"),
        ],
        string="Target Frequency",
        default="monthly",
        required=True,
    )

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    target_commission = fields.Float(
        string="On Target Commission",
        default=0.0,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("done", "Done"),
        ],
        default="draft",
    )

    # ----------------------------------------------------
    # Relationships
    # ----------------------------------------------------

    commission_ids = fields.One2many(
        "sales.commission",
        "plan_id",
        string="Commissions",
    )

    achievement_ids = fields.One2many(
        "sales.commission.achievement",
        "plan_id",
        string="Achievements",
    )

    target_ids = fields.One2many(
        "sales.commission.target",
        "plan_id",
        string="Targets",
    )
    
    period_ids = fields.One2many(
        "sales.commission.period",
        "plan_id",
        string="Periods",
    )

    salesperson_ids = fields.One2many(
        "sales.commission.salesperson",
        "plan_id",
        string="Sales People",
    )

    # ----------------------------------------------------
    # Auto Generate Target Periods (Onchange for UI)
    # ----------------------------------------------------

    @api.onchange("start_date", "end_date", "periodicity")
    def _onchange_generate_targets(self):
        if not self.start_date or not self.end_date:
            return

        self.target_ids = [(5, 0, 0)]
        self.period_ids = [(5, 0, 0)]

        periods = []
        targets = []
        current = self.start_date

        if self.periodicity == "monthly":
            while current <= self.end_date:
                last_day = calendar.monthrange(current.year, current.month)[1]
                name = current.strftime("%B %Y")
                date_from = current
                date_to = current.replace(day=last_day)

                periods.append((0, 0, {
                    "name": name,
                    "date_from": date_from,
                    "date_to": date_to,
                }))

                targets.append((0, 0, {
                    "name": name,
                    "date_from": date_from,
                    "date_to": date_to,
                    "target_amount": 0.0,
                }))

                current += relativedelta(months=1)
                current = current.replace(day=1)

        elif self.periodicity == "quarterly":
            while current <= self.end_date:
                quarter = ((current.month - 1) // 3) + 1
                start_month = (quarter - 1) * 3 + 1
                start = date(current.year, start_month, 1)
                end = start + relativedelta(months=3) - relativedelta(days=1)
                name = f"{current.year} Q{quarter}"

                periods.append((0, 0, {
                    "name": name,
                    "date_from": start,
                    "date_to": end,
                }))

                targets.append((0, 0, {
                    "name": name,
                    "date_from": start,
                    "date_to": end,
                    "target_amount": 0.0,
                }))

                current = start + relativedelta(months=3)

        elif self.periodicity == "yearly":
            name = str(self.start_date.year)
            date_from = date(self.start_date.year, 1, 1)
            date_to = date(self.start_date.year, 12, 31)

            periods.append((0, 0, {
                "name": name,
                "date_from": date_from,
                "date_to": date_to,
            }))

            targets.append((0, 0, {
                "name": name,
                "date_from": date_from,
                "date_to": date_to,
                "target_amount": 0.0,
            }))

        # Correctly assigning the generated periods/targets to the fields
        self.period_ids = periods
        self.target_ids = targets
        
        
        # ----------------------------------------------------
# Enterprise: Sync On Target Commission
# ----------------------------------------------------

    @api.onchange("target_commission")
    def _onchange_target_commission(self):
        """
        Whenever the On Target Commission changes:
        - If no commission levels exist yet, auto-create the
          standard 0% / 50% / 100% levels (matching Enterprise),
          with only the 100% level pre-filled with the amount.
        - If levels already exist, just keep the 100% level's
          commission amount in sync with the target commission.
        """
        for plan in self:
            if not plan.commission_ids:
                plan.commission_ids = [
                    (0, 0, {
                        "target_completion": 0,
                        "commission": 0.0,
                        "otc": 0.0,
                    }),
                    (0, 0, {
                        "target_completion": 50,
                        "commission": 0.0,
                        "otc": 0.0,
                    }),
                    (0, 0, {
                        "target_completion": 100,
                        "commission": plan.target_commission,
                        "otc": 0.0,
                    }),
                ]
                continue

            level = plan.commission_ids.filtered(
                lambda c: c.target_completion == 100
            )[:1]

            if level:
                level.commission = plan.target_commission

    # ----------------------------------------------------
    # Workflow Actions
    # ----------------------------------------------------

    def action_approve(self):
        for plan in self:
            plan.state = "approved"
            plan._generate_commission_records()

        return True

    def _generate_commission_records(self):
        CommissionRecord = self.env["sales.commission.record"]

        for plan in self:
            for salesperson in plan.salesperson_ids:
                for target in plan.target_ids:

                    # Check if a record already exists
                    existing_record = CommissionRecord.search([
                        ("plan_id", "=", plan.id),
                        ("salesperson_id", "=", salesperson.user_id.id),
                        ("target_id", "=", target.id),
                    ], limit=1)

                    if existing_record:
                        continue

                    CommissionRecord.create({
                        "plan_id": plan.id,
                        "salesperson_id": salesperson.user_id.id,
                        "target_id": target.id,
                        "achieved": 0.0,
                        "commission": 0.0,
                        "state": "draft",
                    })

    def action_done(self):
        self.write({"state": "done"})

    def action_reset_draft(self):
        self.write({"state": "draft"})

    # ----------------------------------------------------
    # Buttons / Utility Methods
    # ----------------------------------------------------

    def action_add_multiple_salespersons(self):
        return True

    def action_add_commission_level(self):
        self.ensure_one()
        self.env["sales.commission"].create({
            "plan_id": self.id,
            "target_completion": 0,
            "commission": 0,
            "otc": 0,
        })
        return True

    def action_commission_table(self):
        return True

    # ----------------------------------------------------
    # Backend Target Generation (Used by Create/Write)
    # ----------------------------------------------------

    def _generate_targets(self):
        for rec in self:
            if not rec.start_date or not rec.end_date:
                continue

            # Clear existing targets linked to this plan
            rec.target_ids.unlink()

            targets = []
            current = rec.start_date

            if rec.periodicity == "monthly":
                while current <= rec.end_date:
                    last_day = calendar.monthrange(current.year, current.month)[1]
                    targets.append({
                        "plan_id": rec.id,
                        "name": current.strftime("%B %Y"),
                        "date_from": current,
                        "date_to": current.replace(day=last_day),
                        "target_amount": 0.0,
                    })
                    current += relativedelta(months=1)
                    current = current.replace(day=1)

            elif rec.periodicity == "quarterly":
                while current <= rec.end_date:
                    quarter = ((current.month - 1) // 3) + 1
                    start_month = (quarter - 1) * 3 + 1
                    start = date(current.year, start_month, 1)
                    end = start + relativedelta(months=3) - relativedelta(days=1)

                    targets.append({
                        "plan_id": rec.id,
                        "name": f"{current.year} Q{quarter}",
                        "date_from": start,
                        "date_to": end,
                        "target_amount": 0.0,
                    })
                    current = start + relativedelta(months=3)

            elif rec.periodicity == "yearly":
                targets.append({
                    "plan_id": rec.id,
                    "name": str(rec.start_date.year),
                    "date_from": date(rec.start_date.year, 1, 1),
                    "date_to": date(rec.start_date.year, 12, 31),
                    "target_amount": 0.0,
                })

            if targets:
                self.env["sales.commission.target"].create(targets)

    # ----------------------------------------------------
    # Odoo Crud Overrides
    # ----------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        records._generate_targets()

        for plan in records:
            level = plan.commission_ids.filtered(
                lambda c: c.target_completion == 100
            )[:1]

            if level:
                level.write({
                    "commission": plan.target_commission,
                })

        return records

    def write(self, vals):
        result = super().write(vals)

        # Whenever a plan's state becomes "approved" -- whether via the
        # Approve button (action_approve) or a direct click on the
        # "Approved" bubble in the statusbar -- make sure commission
        # records exist. Safe to call repeatedly: it skips any records
        # that already exist.
        if vals.get("state") == "approved":
            self._generate_commission_records()

        # NOTE: target_ids are now generated live by the
        # _onchange_generate_targets() onchange when editing through
        # the form, and are saved as part of the normal write() above.
        # We intentionally do NOT call _generate_targets() here anymore:
        # doing so on top of the onchange-supplied target_ids caused a
        # double unlink/recreate in the same transaction, which could
        # leave target lines without a date_from. _generate_targets()
        # is still called from create() to cover records made via
        # API/import that never go through the form's onchange.

        if "target_commission" in vals:
            for plan in self:
                level = plan.commission_ids.filtered(
                    lambda c: c.target_completion == 100
                )[:1]

                if level:
                    level.write({
                        "commission": plan.target_commission,
                    })

        return result
    
    def _sync_commission_records(self):
        CommissionRecord = self.env["sales.commission.record"]

        for plan in self:
            # All valid combinations
            valid_pairs = set()

            for salesperson in plan.salesperson_ids:
                for target in plan.target_ids:
                    valid_pairs.add((salesperson.user_id.id, target.id))

                    existing = CommissionRecord.search([
                        ("plan_id", "=", plan.id),
                        ("salesperson_id", "=", salesperson.user_id.id),
                        ("target_id", "=", target.id),
                    ], limit=1)

                    if not existing:
                        CommissionRecord.create({
                            "plan_id": plan.id,
                            "salesperson_id": salesperson.user_id.id,
                            "target_id": target.id,
                            "achieved": 0.0,
                            "commission": 0.0,
                            "state": "draft",
                        })

            # Optional cleanup
            records = CommissionRecord.search([
                ("plan_id", "=", plan.id),
            ])

            for rec in records:
                pair = (rec.salesperson_id.id, rec.target_id.id)
                if pair not in valid_pairs:
                    rec.unlink()