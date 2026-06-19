# -*- coding: utf-8 -*-
{
    'name': 'Website Event QR Theming Snippet',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Add a customizable Event QR code snippet to the Website Builder.',
    'description': """
        Allows users to drag and drop a dynamic Event QR block into Website pages.
        Includes controls to theme the QR code colors, target link, and wrappers.
    """,
    'depends': [
        'website',
        'website_event',
        'event_customizations',
    ],
    'data': [
        'views/snippets_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_event_qr_theming/static/src/scss/snippets.scss',
            'website_event_qr_theming/static/src/js/frontend_qr.js',
        ],
        'website.website_builder_assets': [
            'website_event_qr_theming/static/src/js/snippet_options.js',
            'website_event_qr_theming/static/src/js/snippet_options.xml',
            'website_event_qr_theming/static/src/website_builder/event_qr_page_option.js',
            'website_event_qr_theming/static/src/website_builder/event_qr_page_option.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
