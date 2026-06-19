# -*- coding: utf-8 -*-
{
    'name': 'Email Marketing: Event QR Theming Snippet',
    'version': '19.0.1.0.0',
    'category': 'Marketing/Email Marketing',
    'summary': 'Add a customizable Event QR code block to the email builder.',
    'description': """
        Allows marketers to drag and drop a dynamic Event QR block into campaign emails.
        Includes controls to theme the QR code colors and card wrappers.
    """,
    'depends': [
        'mass_mailing',
        'event_customizations',
    ],
    'data': [
        'views/snippets_templates.xml',
    ],
    'assets': {
        # SCSS applied inside the mail editor iframe
        'mass_mailing.assets_iframe_style': [
            'emailmarketing_event_qr_theming/static/src/scss/snippets.scss',
        ],
        # JS option component loaded in the builder editor options
        'mass_mailing.assets_builder': [
            'emailmarketing_event_qr_theming/static/src/js/snippet_options.js',
            'emailmarketing_event_qr_theming/static/src/js/snippet_options.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
