{
    'name': 'Graphic Designer Workflow',
    'version': '19.0.2.0.0',
    'category': 'Customizations',
    'depends': ['base', 'product', 'website_sale', 'survey', 'stock'],
    'data': [
        'security/graphic_designer_groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/mail_templates.xml',
        'views/product_template_views.xml',
        'views/product_approval_views.xml',
        'views/menu_overrides.xml',
        'views/product_form_custom.xml',
        'views/survey_question_views.xml',
        'wizard/reject_reason_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'graphic_designer_workflow/static/src/xml/product_image_picker.xml',
            'graphic_designer_workflow/static/src/js/product_image_picker.js',
        ],
    },
    'installable': True,
    'application': False,
}