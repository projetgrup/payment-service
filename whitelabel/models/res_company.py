# -- coding: utf-8 --
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

import os

from odoo import api, models, fields, tools
from odoo.tools.image import image_data_uri


class ResCompany(models.Model):
    _inherit = 'res.company'

    #mail_powered_by = fields.Boolean('Mail Powered By', default=True)

    @api.model
    def reset_company_logo(self):
        order_objs = self.search([])
        for order_obj in order_objs:
            order_obj.logo = open(
                os.path.join(tools.config['root_path'], 'addons', 'base', 'res', 'res_company_logo.png'),
                'rb').read().encode('base64')

    def get_logo_data_url(self):
        url = image_data_uri(self.logo)
        return url
