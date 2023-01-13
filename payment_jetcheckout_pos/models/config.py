# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_pos_jetcheckout = fields.Boolean(string="Jetcheckout Payment Terminal", help="The transactions are processed by Jetcheckout. Set your Jetcheckout credentials on the related payment method.")
