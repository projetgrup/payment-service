# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AuthOAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    company_id = fields.Many2one('res.company')

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        should_filter_company = False
        if domain:
            for d in domain:
                if d[0] == 'enabled':
                    should_filter_company = True
                    break
        if should_filter_company:
            domain = [('company_id', '=', self.env.company.id)] + domain
        return super().search_read(domain, fields, offset, limit, order)
