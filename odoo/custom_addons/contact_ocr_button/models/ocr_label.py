from odoo import models, fields

class OcrLabel(models.Model):
    _name = 'ocr.label'
    _description = 'OCR Field Label'
    _order = 'sequence, name'

    name = fields.Char(string="Label Name", required=True, translate=True)
    sequence = fields.Integer(string="Sequence", default=10)
    target_field = fields.Selection([
        ('unassigned', 'Unassigned'),
        ('name', 'Name'),
        ('email', 'Email'),
        ('phone', 'Phone No'),
        ('mobile', 'Mobile'),
        ('parent_id', 'Company Name'),
        ('function', 'Designation'),
        ('website', 'Website'),
        ('street', 'Street1'),
        ('street2', 'Street2'),
        ('city', 'City'),
        ('state_id', 'State'),
        ('zip', 'Pincode'),
        ('country_id', 'Country'),
        ('vat', 'Tax_id'),
        ('title', 'Title'),
        ('category_id', 'Tags'),
    ], string="Target Field", default='unassigned', required=True,
       help="The corresponding field on the Contact form that this label should update.")
