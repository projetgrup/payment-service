# -*- coding: utf-8 -*-
from odoo import models, SUPERUSER_ID

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def load_web_menus(self, debug):
        if 'system' in self.env.context:
            self.invalidate_cache()
            self.clear_caches()
        return super().load_web_menus(debug)

    def get_user_roots(self):
        if not self.env.uid == SUPERUSER_ID and self.env.context.get('system'):
            return self.env.ref('base.menu_board_root')
        return super().get_user_roots()
