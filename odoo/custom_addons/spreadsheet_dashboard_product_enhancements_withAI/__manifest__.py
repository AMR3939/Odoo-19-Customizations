# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Spreadsheet_dashboard_product_enhancements_withAI',

    'version': '19.0.1.0.0',

    'category': 'Productivity/Dashboard',

    'summary': 'Enhancements for the Odoo Product dashboard',

    'description': """
Spreadsheet Dashboard Product Enhancements
===========================================

This custom module enhances the standard Odoo Product
spreadsheet dashboard.

Features:

1. Adds Least Seller scorecard.
2. Adds Least Category scorecard.
3. Adds percentage of revenue to the Best Selling Products table.

The standard Odoo dashboard module is not modified directly.
The existing spreadsheet dashboard JSON is patched through
a post-init hook.
""",

    'depends': [
        'spreadsheet_dashboard_sale',
    ],

    'data': [],

    'post_init_hook': '_post_init_hook',

    'installable': True,

    'application': False,

    'auto_install': False,

    'author': 'Alwin',

    'license': 'LGPL-3',
}