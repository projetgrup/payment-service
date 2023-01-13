# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    syncops_url = fields.Char(string='syncOPS Endpoint URL', config_parameter='syncops.url')
