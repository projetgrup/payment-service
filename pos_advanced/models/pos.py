# -*- coding: utf-8 -*-
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    jetcheckout_cash_payment_limit_ok = fields.Boolean(string='Limit Cash Payment Amount')
    jetcheckout_cash_payment_limit_amount = fields.Monetary(string='Cash Payment Amount Limit')
