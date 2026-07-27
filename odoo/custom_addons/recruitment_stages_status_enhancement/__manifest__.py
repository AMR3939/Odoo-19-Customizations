# -*- coding: utf-8 -*-

{
    "name": "Intern Recruitment Workflow",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "summary": "Independent intern recruitment workflow with sequential stage movement",
    "description": """
Intern Recruitment Workflow
===========================

This module creates an independent Intern Recruitment system without modifying
Odoo's default Recruitment module.

Main Features
-------------
- Separate Intern Job Positions
- Separate Intern Applications
- Separate Intern Workflow Stages
- Sequence-based stage movement
- Move to Next Stage / Move to Previous Stage workflow
- Reject flow
- Workflow history tracking
- Contact creation
- Employee creation from selected intern applicant
- Post-hiring intern lifecycle stages
- Website intern application pages

Important
---------
This module does not modify Odoo's default Recruitment actions, views, stages,
or job positions. Default Recruitment remains untouched.
    """,
    "author": "Arjun P S",
    "website": "",
    "license": "LGPL-3",

    "depends": [
        "hr",
        "hr_recruitment",
        "website",
        "mail",
        "hr_skills",
        "hr_recruitment_skills",
        "hr_customizations",
    ],

    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",

        "data/sequence.xml",
        "data/stage_data.xml",
        "data/mail_template.xml",

        "views/intern_stage_views.xml",
        "views/intern_job_views.xml",
        "views/intern_applicant_views.xml",
        "views/workflow_history_views.xml",
        "views/website_intern_recruitment_templates.xml",
        "views/menu.xml",
        "views/hr_employee_intern_views.xml",
    ],

    "installable": True,
    "application": False,
    "auto_install": False,
}