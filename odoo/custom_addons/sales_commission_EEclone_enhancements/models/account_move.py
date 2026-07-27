from odoo import models
import logging

_logger = logging.getLogger(__name__)

_logger.warning(">>>>>>>> account_move.py LOADED <<<<<<<<")


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=False):

        _logger.warning("******** _post CALLED ********")

        res = super()._post(soft=soft)

        for move in self:

            _logger.warning(
                "Move=%s  Type=%s  State=%s",
                move.name,
                move.move_type,
                move.state,
            )

            if move.move_type != "out_invoice":
                continue

            _logger.warning("Customer Invoice Found")
            _logger.warning("Invoice Amount : %s", move.amount_total)
            _logger.warning("Salesperson : %s", move.invoice_user_id.name)
            
            # --------------------------------------------------
            # Find Commission Plan
            # --------------------------------------------------

            assignment = self.env[
                "sales.commission.salesperson"
            ].search(
                [
                    ("user_id", "=", move.invoice_user_id.id),
                ],
                limit=1,
            )

            if not assignment:
                _logger.warning(
                    "No Commission Plan assigned."
                )
                continue

            _logger.warning(
                "Commission Plan : %s",
                assignment.plan_id.name,
            )
            
                        # --------------------------------------------------
            # Find Current Target Period
            # --------------------------------------------------

            target = self.env["sales.commission.target"].search(
                [
                    ("plan_id", "=", assignment.plan_id.id),
                    ("date_from", "<=", move.invoice_date),
                    ("date_to", ">=", move.invoice_date),
                ],
                limit=1,
            )

            if not target:
                _logger.warning(
                    "No Target Period Found."
                )
                continue

            _logger.warning(
                "Target Period : %s",
                target.name,
            )

            _logger.warning(
                "Target Amount : %s",
                target.target_amount,
            )
            
            _logger.warning("Searching Commission Record...")
            
            # --------------------------------------------------
            # Find Existing Commission Record
            # --------------------------------------------------

            commission_record = self.env[
                "sales.commission.record"
            ].search(
                [
                    ("plan_id", "=", assignment.plan_id.id),
                    ("salesperson_id", "=", move.invoice_user_id.id),
                    ("target_id", "=", target.id),
                ],
                limit=1,
            )
            
            _logger.warning("Checking if record exists...")

            # --------------------------------------------------
            # Create Record if it doesn't exist
            # --------------------------------------------------

            if not commission_record:
                _logger.warning("Creating Commission Record...")

                commission_record = self.env[
                    "sales.commission.record"
                ].create({
                    "plan_id": assignment.plan_id.id,
                    "salesperson_id": move.invoice_user_id.id,
                    "target_id": target.id,
                    "achieved": 0.0,
                })

                _logger.warning(
                    "Commission Record Created : %s",
                    commission_record.id,
                )

            # -----------------------------------------
            # Update the achieved amount.
            # Writing "achieved" triggers _compute_commission()
            # on sales.commission.record automatically (it depends
            # on achieved/achieved_rate), so the tiered/interpolated
            # engine there is the single source of truth for the
            # commission amount. Do not set "commission" here.
            # -----------------------------------------

            _logger.warning("Updating Achieved...")

            commission_record.write({
                "achieved": commission_record.achieved + move.amount_total,
            })

            _logger.warning(
                "Updated Achieved : %s",
                commission_record.achieved,
            )
            _logger.warning(
                "Commission (auto-computed) : %s",
                commission_record.commission,
            )

            # --------------------------------------------------
            # Log this invoice's contribution as an Achievement
            # line (matches the Enterprise "Achievements" report:
            # one row per invoice that fed into a commission
            # record, with a snapshot of the numbers at that time)
            # --------------------------------------------------

            self.env["sales.commission.achievement.line"].create({
                "salesperson_id": move.invoice_user_id.id,
                "plan_id": assignment.plan_id.id,
                "commission_record_id": commission_record.id,
                "target_id": target.id,
                "move_id": move.id,
                "period": target.name,
                "commission_target": target.target_amount,
                "target": target.target_amount,
                "achieved_rate": commission_record.achieved_rate,
                "commission_rate": commission_record.achieved_rate,
                "achieved": move.amount_total,
                "source": "%s (%s)" % (
                    move.name or "",
                    move.invoice_origin or "",
                ),
                "partner_id": move.partner_id.id,
                "currency_id": move.currency_id.id,
            })

        return res