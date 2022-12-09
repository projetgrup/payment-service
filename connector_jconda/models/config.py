# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    jconda_url = fields.Char(string='jConda Endpoint URL', config_parameter='jconda.url')
