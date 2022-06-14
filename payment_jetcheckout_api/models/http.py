# -*- coding: utf-8 -*-
import werkzeug

from odoo import models
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_translation_frontend_modules_name(cls):
        mods = super(IrHttp, cls)._get_translation_frontend_modules_name()
        return mods + ['payment_jetcheckout_api']

    @classmethod
    def _handle_exception(cls, exception):
        if request.is_frontend and isinstance(exception, werkzeug.exceptions.NotFound):
            return werkzeug.utils.redirect('https://iys.org.tr/404')
        return super(IrHttp, cls)._handle_exception(exception)
