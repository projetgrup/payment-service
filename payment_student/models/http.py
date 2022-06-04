# -*- coding: utf-8 -*-
from odoo import models

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_translation_frontend_modules_name(self):
        mods = super(IrHttp, self)._get_translation_frontend_modules_name()
        return mods + ['payment_student']

    def session_info(self):
        res = super(IrHttp, self).session_info()
        if res['user_context'].get('system') == 'student':
            res['home_action_id'] = self.env.ref('payment_student.action_child').id
        return res
