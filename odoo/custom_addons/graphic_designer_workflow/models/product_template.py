from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('first_approval', 'First Approval'),
        ('second_approval', 'Second Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived')
    ], string='Approval Status', default='draft', tracking=True, copy=False)

    rejection_reason = fields.Text(string='Rejection Reason', tracking=True)
    is_design_manager = fields.Boolean(compute='_compute_workflow_roles')
    is_ecommerce_head = fields.Boolean(compute='_compute_workflow_roles')

    @api.depends_context('uid')
    def _compute_workflow_roles(self):
        user = self.env.user
        is_admin = user._is_admin()
        # Evaluate groups
        is_ecom = user.has_group('graphic_designer_workflow.group_ecommerce_head')
        is_dm_group = user.has_group('graphic_designer_workflow.group_design_manager')
        
        for record in self:
            # Ecommerce head is true if they have the group
            record.is_ecommerce_head = is_ecom or is_admin
            # Design manager is true if they have the group AND are NOT ecommerce head, OR if they are admin
            record.is_design_manager = (is_dm_group and not is_ecom) or is_admin

    def action_submit_for_approval(self):
        for record in self:
            if record.approval_state not in ['draft', 'rejected']:
                raise UserError(_("Only draft or rejected products can be submitted for approval."))
            record.approval_state = 'first_approval'

    def action_approve_first(self):
        user = self.env.user
        # Restricted via view groups, but double checked here
        if not user.has_group('graphic_designer_workflow.group_design_manager') or (user.has_group('graphic_designer_workflow.group_ecommerce_head') and not user._is_admin()):
            raise UserError(_("Only a Design Manager can perform the first approval."))
        for record in self:
            if record.approval_state != 'first_approval':
                raise UserError(_("Product is not waiting for first approval."))
            record.approval_state = 'second_approval'

    def action_approve_second(self):
        if not self.env.user.has_group('graphic_designer_workflow.group_ecommerce_head'):
            raise UserError(_("Only the E-Commerce Head can perform the second approval."))
        for record in self:
            if record.approval_state != 'second_approval':
                raise UserError(_("Product is not waiting for second approval."))
            record.approval_state = 'approved'

    def action_reject(self):
        return {
            'name': _('Reject Reason'),
            'type': 'ir.actions.act_window',
            'res_model': 'reject.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id}
        }

    def action_archive_custom(self):
        if not self.env.user.has_group('graphic_designer_workflow.group_ecommerce_head'):
            raise UserError(_("Only the E-Commerce Head can archive products."))
        for record in self:
            if record.approval_state not in ['approved', 'rejected']:
                raise UserError(_("You can only archive products that have already been Approved or Rejected."))
            record.approval_state = 'archived'
            record.active = False

    def action_reset_to_draft(self):
        for record in self:
            if record.approval_state != 'rejected':
                raise UserError(_("Only rejected products can be reset to draft."))
            record.approval_state = 'draft'

    def write(self, vals):
        """ Enforce workflow state restrictions for Graphic Designers. """
        user = self.env.user
        is_manager_or_head = user.has_group('graphic_designer_workflow.group_design_manager') or \
                             user.has_group('graphic_designer_workflow.group_ecommerce_head') or \
                             user.has_group('stock.group_stock_manager') or \
                             user._is_admin()
                             
        for rec in self:
            # Only restrict if they are a Designer and NOT a higher role
            if user.has_group('graphic_designer_workflow.group_graphic_designer') and not is_manager_or_head:
                # Designers can only edit in Draft or Rejected state.
                # Record rules already ensure they only edit their OWN records.
                if rec.approval_state not in ['draft', 'rejected'] and 'approval_state' not in vals:
                    raise UserError(_("Access Restricted: You can only edit your products in Draft or Rejected state."))
        return super().write(vals)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_submit_for_approval(self):
        return self.mapped('product_tmpl_id').action_submit_for_approval()

    def action_approve_first(self):
        return self.mapped('product_tmpl_id').action_approve_first()

    def action_approve_second(self):
        return self.mapped('product_tmpl_id').action_approve_second()

    def action_reject(self):
        if not self:
            return
        return {
            'name': _('Reject Reason'),
            'type': 'ir.actions.act_window',
            'res_model': 'reject.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self[0].product_tmpl_id.id}
        }

    def action_archive_custom(self):
        return self.mapped('product_tmpl_id').action_archive_custom()

    def action_reset_to_draft(self):
        return self.mapped('product_tmpl_id').action_reset_to_draft()