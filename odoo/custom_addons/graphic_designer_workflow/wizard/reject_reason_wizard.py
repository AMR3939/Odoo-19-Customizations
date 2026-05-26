from odoo import models, fields, api

class RejectReasonWizard(models.TransientModel):
    _name = 'reject.reason.wizard'
    _description = 'Reject Reason Wizard'

    product_id = fields.Many2one('product.template', string='Product', required=True)
    reject_reason = fields.Text(string='Reason', required=True)

    def action_confirm_reject(self):
        self.product_id.write({
            'approval_state': 'rejected',
            'rejection_reason': self.reject_reason
        })
