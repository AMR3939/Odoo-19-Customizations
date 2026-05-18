{
    'name': 'Enhanced Recruitment',
    'version': '19.0.1.3',
    'summary': 'Adds advanced education fields and features to Recruitment.',
    'author': 'Selva vignesh',
    'category': 'Human Resources/Recruitment',
    'depends': [
        'hr_recruitment',
        'contact_enhancements', # CRITICAL DEPENDENCY
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_stream_view.xml',
        # 'views/res_city_view.xml', # REMOVED: This view is handled by contact_enhancements
        'views/res_university_view.xml',
        'views/hr_applicant_view.xml',
        'views/hr_applicant_search_view.xml',
        'views/recruitment_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}