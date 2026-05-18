{
    'name': 'HR Employee Customizations',
    'version': '19.0.4.0.0',
    'summary': 'Adds structured education and location fields to Employees.',
    'author': 'G Selva vignesh',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',

    'depends': [
        'hr',
        #'hr_contract',
        'contact_enhancements', # CRITICAL DEPENDENCY
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/configuration_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_employee_search_views.xml',
        'views/hr_menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'hr_customizations/static/src/scss/custom_hr.scss',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}