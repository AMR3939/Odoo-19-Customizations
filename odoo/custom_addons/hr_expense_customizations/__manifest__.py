# -*- coding: utf-8 -*-

{
    'name': 'HR Expense Customizations',

    'version': '19.0.1.0.0',

    'summary': 'Custom HR Expense Approval Workflow',

    'category': 'Human Resources',

    'author': 'Your Company',

    'depends': [
        'hr_expense',
    ],

    'data': [
        'security/hr_expense_security.xml',
        'views/hr_expense_views.xml',
    ],

    
    'assets': {
    'web.assets_backend': [
        'hr_expense_customizations/static/src/scss/hr_expense_customizations.scss',
    ],
},

    'installable': True,

    'application': False,

    'license': 'LGPL-3',
}