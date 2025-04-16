# -*- coding: utf-8 -*-
import base64
import hashlib
from odoo import models, fields

def get_main_company(company):
    if not company.sec_dlp_tag and company.parent_id:
        return get_main_company(company.parent_id)
    return company


class ResCompany(models.Model):
    _inherit = 'res.company'

    sec_dlp_ok = fields.Boolean('Enable DLP')
    sec_dlp_tag = fields.Char('DLP Tag')

    def get_dlp_tag(self, value=None):
        if value:
            hashed = hashlib.sha256(value.encode('utf-8')).digest()
            return base64.b64encode(hashed).decode('utf-8')
        else:
            company = get_main_company(self)
            return company.sec_dlp_tag or ''
