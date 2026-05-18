from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # =====================================================
    # Education Fields
    # =====================================================

    degree_id = fields.Many2one(
        'hr.employee.degree',
        string='Degree',
        tracking=True
    )

    stream_id = fields.Many2one(
        'hr.employee.stream',
        string='Stream',
        tracking=True
    )

    university_id = fields.Many2one(
        'hr.employee.university',
        string='University',
        tracking=True
    )

    # =====================================================
    # Address Fields
    # =====================================================

    place_of_birth_id = fields.Many2one(
        'hr.employee.place_of_birth',
        string='Place of Birth',
        tracking=True
    )

    work_city_id = fields.Many2one(
        'res.city',
        related='address_id.city_id',
        string="Work City",
        store=True,
        readonly=True
    )

    work_country_id = fields.Many2one(
        'res.country',
        related='address_id.country_id',
        string="Work Country",
        store=True,
        readonly=True
    )

    pob_city_id = fields.Many2one(
        'res.city',
        related='place_of_birth_id.city_id',
        string="PoB City",
        store=True,
        readonly=True
    )

    pob_country_id = fields.Many2one(
        'res.country',
        related='place_of_birth_id.country_id',
        string="PoB Country",
        store=True,
        readonly=True
    )

    country_of_birth = fields.Many2one(
        'res.country',
        related='place_of_birth_id.country_id',
        string="Country of Birth",
        store=True,
        readonly=True
    )

    # =====================================================
    # Employee Name Fields
    # =====================================================

    first_name = fields.Char(
        string="First Name",
        tracking=True,
        size=20,
        default=""
    )

    middle_name = fields.Char(
        string="Middle Name",
        tracking=True,
        size=20,
        default=""
    )

    last_name = fields.Char(
        string="Last Name",
        tracking=True,
        size=20,
        default=""
    )

    # =====================================================
    # Emergency Contact Fields
    # =====================================================

    emergency_contact_2 = fields.Char(
        string="Emergency Contact 2"
    )

    emergency_phone_2 = fields.Char(
        string="Emergency Phone 2"
    )

    # =====================================================
    # Resume Fields
    # =====================================================

    resume_doc = fields.Binary(
        string="Curriculum Vitae",
        attachment=True
    )

    resume_filename = fields.Char(
        string="Resume Filename"
    )

    resume_url = fields.Char(
        string="Resume URL",
        compute="_compute_resume_url",
        store=False
    )

    # =====================================================
    # Compute Methods
    # =====================================================

    @api.depends(
        'resume_doc',
        'resume_filename'
    )
    def _compute_resume_url(self):

        for record in self:

            if record.resume_doc:

                attachment = self.env[
                    'ir.attachment'
                ].search([
                    ('res_model', '=', 'hr.employee'),
                    ('res_id', '=', record.id),
                    ('name', '=', record.resume_filename),
                ], limit=1)

                if not attachment:

                    attachment = self.env[
                        'ir.attachment'
                    ].create({
                        'name': record.resume_filename,
                        'type': 'binary',
                        'datas': record.resume_doc,
                        'res_model': 'hr.employee',
                        'res_id': record.id,
                        'mimetype': 'application/pdf',
                    })

                record.resume_url = (
                    f'/web/content/'
                    f'{attachment.id}'
                    f'?download=false'
                )

            else:
                record.resume_url = False

    # =====================================================
    # Constraints
    # =====================================================

    @api.constrains(
        'first_name',
        'middle_name',
        'last_name'
    )
    def _check_name_length(self):

        for record in self:

            if len(record.first_name or '') > 20:
                raise ValidationError(
                    "First Name Max Limit: 20"
                )

            if len(record.middle_name or '') > 20:
                raise ValidationError(
                    "Middle Name Max Limit: 20"
                )

            if len(record.last_name or '') > 20:
                raise ValidationError(
                    "Last Name Max Limit: 20"
                )

    @api.constrains(
        'resume_doc',
        'resume_filename'
    )
    def _check_resume_file(self):

        for record in self:

            if (
                record.resume_doc
                and record.resume_filename
            ):

                if not record.resume_filename.lower().endswith('.pdf'):

                    raise ValidationError(
                        "Only PDF files are allowed for the CV."
                    )

    # =====================================================
    # Onchange
    # =====================================================

    @api.onchange(
        'first_name',
        'middle_name',
        'last_name'
    )
    def _onchange_employee_name(self):

        for record in self:

            record.name = " ".join(
                filter(
                    None,
                    [
                        record.first_name,
                        record.middle_name,
                        record.last_name,
                    ]
                )
            )

    # =====================================================
    # Create Override (FIXED FOR ODOO 19)
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            # Auto-generate employee name
            if not vals.get('name'):

                vals['name'] = " ".join(
                    filter(
                        None,
                        [
                            vals.get('first_name', ''),
                            vals.get('middle_name', ''),
                            vals.get('last_name', ''),
                        ]
                    )
                ).strip()

            # Default resume filename
            if (
                vals.get('resume_doc')
                and not vals.get('resume_filename')
            ):

                vals['resume_filename'] = (
                    'Uploaded_Resume.pdf'
                )

        return super().create(vals_list)

    # =====================================================
    # Write Override
    # =====================================================

    def write(self, vals):

        for record in self:

            updated_vals = vals.copy()

            if any(
                key in vals
                for key in [
                    'first_name',
                    'middle_name',
                    'last_name'
                ]
            ):

                updated_vals['name'] = " ".join(
                    filter(
                        None,
                        [
                            vals.get(
                                'first_name',
                                record.first_name
                            ),

                            vals.get(
                                'middle_name',
                                record.middle_name
                            ),

                            vals.get(
                                'last_name',
                                record.last_name
                            ),
                        ]
                    )
                ).strip()

            if (
                vals.get('resume_doc')
                and not vals.get('resume_filename')
            ):

                updated_vals['resume_filename'] = (
                    'Uploaded_Resume.pdf'
                )

            super(HrEmployee, record).write(updated_vals)

        return True

    # =====================================================
    # Actions
    # =====================================================

    def action_view_pdf(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': self.resume_filename,
            'res_model': 'hr.employee',
            'view_mode': 'form',
            'views': [
                (
                    self.env.ref(
                        'hr_customizations.view_pdf_popup'
                    ).id,
                    'form'
                )
            ],
            'target': 'new',
            'res_id': self.id,
        }