{
    'name': 'Social Sharing',
    'category': 'Website',
    'version': '19.0.1.0.0',
    'author': 'GoGaga Entertainments Pvt. Ltd.',
    'depends': ['website', 'website_blog', 'website_sale'],
    'data': [
        'views/blog_share_inject.xml',
        'views/product_share_inject.xml',
        'views/s_social_media_override.xml',
        'views/snippets/s_social_share_vertical.xml',
        'views/snippets/s_social_share_horizontal.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'social_sharing/static/src/css/social_sharing.css',
            'social_sharing/static/src/js/social_sharing.js',
        ],
        # Fix excessive whitespace on Map/Google Map snippet thumbnail cards
        # in the Website Builder "Insert a block" panel (snippet preview iframe).
        'html_builder.iframe_add_dialog': [
            'social_sharing/static/src/css/snippet_preview.css',
        ],
    },
    'license': 'LGPL-3',
}
