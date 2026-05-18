{
    'name': 'Contact Enhancements & Dashboard',
    'version': '19.0.3.1', # Version bump for the fix
    'summary': 'Centralized City/State/Country model and Contact Analysis Dashboard.',
    'description': """
        - Establishes a central, structured model for addresses (Country > State > City) to be used by all other modules.
        - Enhances the Contact form with a smart city dropdown that auto-populates State and Country.
        - Ensures maximum compatibility with other modules by not enforcing database-level constraints on addresses.
        - Provides a fully functional Contact Analysis Dashboard.
    """,
    'category': 'Sales/CRM',
    'author': 'Your Name',
    'depends': [
        'contacts',
        'base',
        'web',
    ],
    'data': [

        'views/res_city_views.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/contact_dashboard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}