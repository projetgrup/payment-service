# -*- coding: utf-8 -*-
from odoo import models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def get_user_roots(self):
        res = super().get_user_roots()
        if self.env.context.get('system') == 'insurance':
            res |= self.env.ref('payment_insurance.menu_main')
        return res
