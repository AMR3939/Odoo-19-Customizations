from odoo import models, fields, api


class SurveyQuestionSelectedImage(models.Model):
    _name = 'survey.question.selected.image'
    _description = 'Survey Question Selected Image'
    _order = 'sequence, id'

    question_id = fields.Many2one(
        'survey.question',
        string='Question',
        ondelete='cascade',
        required=True,
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)

    image = fields.Image(
        string='Image',
        attachment=False,
        max_width=1920,
        max_height=1920,
    )

    # Not computed — written explicitly so it works both during onchange
    # (where we set a product URL for preview) and after save (where
    # _sync_selected_images sets the /web/image/.../ route).
    image_url = fields.Char(string='Image URL', readonly=True)

    image_type = fields.Selection([
        ('product', 'Product Main Image'),
        ('variant', 'Variant Image'),
        ('ecommerce', 'E-commerce Media'),
    ], string='Type', readonly=True)

    name = fields.Char(string='Label', readonly=True)
    selected = fields.Boolean(string='Include', default=True)
    def write(self, vals):
        res = super().write(vals)
        if 'selected' in vals:
            # Trigger recompute of description_with_images on parent questions
            questions = self.mapped('question_id')
            questions._compute_description_with_images()
        return res