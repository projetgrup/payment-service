# -*- coding: utf-8 -*-
from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def get_base_url(self):
        company_id = self.env.context.get('company') or self.env.company.id
        website = self.env['website'].search([('company_id', '=', company_id)], limit=1)
        url = website and website.domain or super().get_base_url() or ''
        if url and url[-1] == '/':
            url = url[:-1]
        return url or ''
