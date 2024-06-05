# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_translation_frontend_modules_name(self):
        mods = super(IrHttp, self)._get_translation_frontend_modules_name()
        return mods + ['payment_supplier']
