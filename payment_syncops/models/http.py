# -*- coding: utf-8 -*-
from odoo import models


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_translation_frontend_modules_name(self):
        mods = super(Http, self)._get_translation_frontend_modules_name()
        return mods + ['payment_syncops']
