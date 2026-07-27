{
    'name': 'sales_commission_EEclone_enhancements',
    'version': '19.0.1.0.0',
    'depends': ['sale_management', 'sales_team', 'account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',

        'views/commission_views.xml',
        "views/target_views.xml",
        'views/achievement_views.xml',
        'views/achievement_line_views.xml',
        'views/salesperson_views.xml',
        'views/adjustment_views.xml',
        'views/commission_record_views.xml',
        'views/commission_report_views.xml',
        'views/commission_plan_views.xml',

        'report/commission_report_wizard_templates.xml',
        'wizard/commission_report_wizard_views.xml',

        'views/menus.xml',
    ],
    
"assets": {
    "web.assets_backend": [
        "sales_commission_EEclone_enhancements/static/src/components/commission_graph/commission_graph.js",
        "sales_commission_EEclone_enhancements/static/src/components/commission_graph/commission_graph.xml",
        "sales_commission_EEclone_enhancements/static/src/components/commission_graph/commission_graph.scss",
        #"sales_commission_EEclone_enhancements/static/src/js/commission_form_patch.js",
    ],
},
    
    'installable': True,
    'application': True,
}