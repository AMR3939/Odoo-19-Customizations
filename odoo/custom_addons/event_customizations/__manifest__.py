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
        'views/event_event_views.xml',
    ],

    'installable': True,

    'application': False,

    'license': 'LGPL-3',
}