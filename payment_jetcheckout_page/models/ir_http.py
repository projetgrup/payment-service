# -*- coding: utf-8 -*-
from odoo import api, models

class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @api.model
    def get_payment_page_session_info(self):
        return {
            'is_admin': False,
            'is_system': False,
            'is_website_user': False,
            'user_id': False,
            'is_frontend': True,
            'profile_session': False,
            'profile_collectors': False,
            'profile_params': False,
            'show_effect': False,
        }
