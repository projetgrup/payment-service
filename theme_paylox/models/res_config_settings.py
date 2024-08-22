# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    paylox_auto_create_website = fields.Boolean(string='Paylox Create Website Automatically', config_parameter='theme_paylox.auto_create_website')
