# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import base64
import io
import xlrd
import openpyxl


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    # =====================================================
    # Additional Fields
    # =====================================================

    spreadsheet_file = fields.Binary(
        string="Spreadsheet File"
    )

    spreadsheet_filename = fields.Char(
        string="Spreadsheet Filename"
    )

    finance_manager_id = fields.Many2one(
        comodel_name='res.users',
        string="Finance Manager",
        domain=lambda self: [
            (
                'all_group_ids',
                'in',
                [
                    self.env.ref(
                        'hr_expense.group_hr_expense_team_approver'
                    ).id,
                    self.env.ref(
                        'hr_expense_customizations.group_finance_approver'
                    ).id,
                ]
            )
        ],
        copy=False,
        tracking=True,
    )

    # =====================================================
    # Extend State Field
    # =====================================================

    state = fields.Selection(
        selection_add=[
            ('finance_approved', 'Finance Approved'),
        ],
        ondelete={
            'finance_approved': 'cascade',
        },
        tracking=True,
    )

    # =====================================================
    # Spreadsheet Import
    # =====================================================

    def action_import_from_spreadsheet(self):

        self.ensure_one()

        if not self.spreadsheet_file:

            raise ValidationError(
                _("Please upload a spreadsheet file first.")
            )

        file_data = base64.b64decode(
            self.spreadsheet_file
        )

        file_stream = io.BytesIO(file_data)

        try:

            try:

                workbook = xlrd.open_workbook(
                    file_contents=file_stream.read()
                )

                sheet_data = workbook.sheet_by_index(0)

                for row_idx in range(
                    1,
                    sheet_data.nrows
                ):

                    row = sheet_data.row_values(row_idx)

                    self._create_expense_from_row(row)

            except Exception:

                file_stream.seek(0)

                workbook = openpyxl.load_workbook(
                    file_stream
                )

                sheet_data = workbook.active

                for row in sheet_data.iter_rows(
                    min_row=2,
                    values_only=True
                ):

                    self._create_expense_from_row(row)

            return True

        except Exception as error:

            raise ValidationError(
                _(
                    "Error importing spreadsheet: %s"
                ) % str(error)
            )

    # =====================================================
    # Create Expense
    # =====================================================

    def _create_expense_from_row(self, row):

        product_name = row[0]
        description = row[1]
        amount = row[2]
        date = row[3]
        employee_id = row[4]

        product = self.env[
            'product.product'
        ].search([
            ('name', '=', product_name)
        ], limit=1)

        if not product:

            raise ValidationError(
                _("Product not found: %s")
                % product_name
            )

        self.env['hr.expense'].create({
            'product_id': product.id,
            'name': description,
            'date': date,
            'employee_id': employee_id,
            'total_amount_currency': amount,
            'quantity': 1,
            'payment_mode': 'own_account',
        })

    # =====================================================
    # Finance Approval
    # =====================================================

    def action_finance_approve(self):

        for expense in self:

            if expense.state != 'approved':

                raise UserError(
                    _(
                        "Expense must be HR approved first."
                    )
                )

            if (
                expense.finance_manager_id
                and expense.finance_manager_id.id != self.env.uid
            ):

                raise UserError(
                    _(
                        "Only assigned Finance Manager "
                        "can approve."
                    )
                )

            expense.write({
                'state': 'finance_approved'
            })

    # =====================================================
    # Attachment Validation
    # =====================================================

    @api.constrains('attachment_ids')
    def _check_attachments(self):

        for record in self:

            if not record.attachment_ids:

                raise ValidationError(
                    _(
                        "Attach at least one document."
                    )
                )

    # =====================================================
    # Override Approve
    # =====================================================

    def action_approve(self):

        for expense in self:

            if (
                expense.manager_id
                and expense.manager_id.id != self.env.uid
            ):

                raise UserError(
                    _(
                        "Only assigned HR Manager "
                        "can approve."
                    )
                )

        return super().action_approve()

    # =====================================================
    # Move Creation Validation
    # =====================================================

    def _check_can_create_move(self):

        for expense in self:

            if expense.state != 'finance_approved':

                raise UserError(
                    _(
                        "Only Finance Approved expenses "
                        "can create journal entries."
                    )
                )

        return super()._check_can_create_move()