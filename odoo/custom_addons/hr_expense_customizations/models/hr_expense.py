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
        copy=False,
        tracking=True,
        domain=lambda self: [
            ('share', '=', False),
            '|',
            (
                'all_group_ids',
                'in',
                self.env.ref(
                    'hr_expense_customizations.group_finance_approver'
                ).ids
            ),
            (
                'all_group_ids',
                'in',
                self.env.ref(
                    'hr_expense.group_hr_expense_team_approver'
                ).ids
            ),
        ],
    )

    # =====================================================
    # Extend State Field
    # =====================================================

    state = fields.Selection(
        selection_add=[
            ('finance_approved', 'Finance Approved'),
        ],
        ondelete={
            'finance_approved': 'set default',
        },
        tracking=True,
    )

    # =====================================================
    # Finance Manager Domain
    # =====================================================

    @api.onchange('finance_manager_id')
    def _onchange_finance_manager_id(self):

        finance_group = self.env.ref(
            'hr_expense_customizations.group_finance_approver',
            raise_if_not_found=False
        )

        hr_group = self.env.ref(
            'hr_expense.group_hr_expense_team_approver',
            raise_if_not_found=False
        )

        domain = [('share', '=', False)]

        allowed_group_ids = []

        if finance_group:
            allowed_group_ids.extend(finance_group.ids)

        if hr_group:
            allowed_group_ids.extend(hr_group.ids)

        if allowed_group_ids:
            domain.append((
                'all_group_ids',
                'in',
                allowed_group_ids
            ))

        allowed_users = self.env['res.users'].search(domain)

        return {
            'domain': {
                'finance_manager_id': [
                    ('id', 'in', allowed_users.ids)
                ]
            }
        }

    # =====================================================
    # Spreadsheet Import
    # =====================================================

    def action_import_from_spreadsheet(self):

        self.ensure_one()

        if not self.spreadsheet_file:
            raise ValidationError(
                _("Please upload a spreadsheet file first.")
            )

        try:

            file_data = base64.b64decode(
                self.spreadsheet_file
            )

            file_stream = io.BytesIO(file_data)

            # =========================================
            # XLS FILE
            # =========================================

            try:

                workbook = xlrd.open_workbook(
                    file_contents=file_stream.read()
                )

                sheet_data = workbook.sheet_by_index(0)

                for row_idx in range(1, sheet_data.nrows):

                    row = sheet_data.row_values(row_idx)

                    self._create_expense_from_row(row)

            # =========================================
            # XLSX FILE
            # =========================================

            except Exception:

                file_stream.seek(0)

                workbook = openpyxl.load_workbook(
                    file_stream,
                    data_only=True
                )

                sheet_data = workbook.active

                for row in sheet_data.iter_rows(
                    min_row=2,
                    values_only=True
                ):

                    self._create_expense_from_row(row)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Spreadsheet imported successfully.'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as error:

            raise ValidationError(
                _("Error importing spreadsheet: %s")
                % str(error)
            )

    # =====================================================
    # Create Expense From Spreadsheet Row
    # =====================================================

    def _create_expense_from_row(self, row):

        if not row:
            return

        product_name = row[0] if len(row) > 0 else False
        description = row[1] if len(row) > 1 else False
        amount = row[2] if len(row) > 2 else 0.0
        date = row[3] if len(row) > 3 else fields.Date.today()
        employee_id = row[4] if len(row) > 4 else False

        if not product_name:
            raise ValidationError(
                _("Product name is required.")
            )

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

        employee = self.env['hr.employee'].browse(
            int(employee_id)
        ) if employee_id else self.env.user.employee_id

        if not employee:
            raise ValidationError(
                _("Employee not found.")
            )

        self.env['hr.expense'].create({
            'product_id': product.id,
            'name': description or product.display_name,
            'date': date,
            'employee_id': employee.id,
            'total_amount_currency': float(amount or 0.0),
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
                and expense.finance_manager_id != self.env.user
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

        return True

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
    # Override HR Approval
    # =====================================================

    def action_approve(self):

        for expense in self:

            if (
                expense.manager_id
                and expense.manager_id != self.env.user
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