{
    'name': 'Spreadsheet_dashboard_website_sale_enhancements_withAI',
    'version': '1.0.0',
    'category': 'Productivity/Dashboard',
    'summary': 'Enhance the Odoo eCommerce spreadsheet dashboard with additional KPIs and product revenue share.',
    'description': '''
eCommerce Spreadsheet Dashboard Enhancements
============================================

Adds:
1. Average Order Value KPI.
2. Customer Acquisition KPI for logged-in website customers making their first confirmed website purchase.
3. % of Revenue column to the Top Products table.
''',
    'depends': [
        'spreadsheet_dashboard_website_sale',
        'spreadsheet_dashboard',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/dashboards.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'author': 'Custom',
}
