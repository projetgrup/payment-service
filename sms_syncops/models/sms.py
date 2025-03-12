# -*- coding: utf-8 -*-
from odoo import models, fields


class SmsProvider(models.Model):
    _inherit = 'sms.provider'

    syncops_ok = fields.Boolean(string='Use syncOPS')
    syncops_connector_id = fields.Many2one('syncops.connector', string='syncOPS Connector')
    username = fields.Char(required=False)
    password = fields.Char(required=False)
