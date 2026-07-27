from odoo import api, fields, models


class SalesCommissionReportWizard(models.TransientModel):
    _name = "sales.commission.report.wizard"
    _description = "Sales Commission Report Wizard"

    salesperson_id = fields.Many2one(
        comodel_name="res.users",
        string="Sales Person",
        required=True,
    )

    start_date = fields.Date(
        string="Start Date",
        required=True,
    )

    end_date = fields.Date(
        string="End Date",
        required=True,
    )

    def action_print_report(self):
            self.ensure_one()

            records = self.env["sales.commission.record"].search([
                ("salesperson_id", "=", self.salesperson_id.id),
                ("period", ">=", self.start_date),
                ("period", "<=", self.end_date),
            ])

            report_action = self.env.ref(
                "sales_commission_EEclone_enhancements."
                "action_report_sales_commission_wizard"
            )
            return report_action.with_context(
                wizard_salesperson_name=self.salesperson_id.name,
                wizard_start_date=self.start_date,
                wizard_end_date=self.end_date,
            ).report_action(records)