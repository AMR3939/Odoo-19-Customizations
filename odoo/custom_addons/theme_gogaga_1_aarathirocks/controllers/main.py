# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website

class GoGagaWebsite(Website):

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        website = request.website
        if website and website.theme_id and website.theme_id.name == 'theme_gogaga_1_aarathirocks':
            return request.render('theme_gogaga_1_aarathirocks.gogaga_home')
        return super().index(**kw)