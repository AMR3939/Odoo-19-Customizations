# -*- coding: utf-8 -*-

{
    'name': 'Event Customizations',

    'version': '19.0.1.0.0',

    'summary': 'Event QR Code Customizations',

    'category': 'Events',

    'depends': [
        'event',
        'website_event',
    ],

    'assets': {
        'web.assets_backend': [
            'event_customizations/static/src/css/event_style.css',
        ],
    },

    'data': [
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'views/event_event_views.xml',
        'views/res_config_settings_views.xml',
        'views/event_templates.xml',
        'views/event_registration_views.xml'
    ],

    'installable': True,

    'application': False,

    'license': 'LGPL-3',
}