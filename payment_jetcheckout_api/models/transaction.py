# -*- coding: utf-8 -*-
from odoo import fields, models

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    partner_authorized = fields.Char('API Partner Authorized', readonly=True)
    jetcheckout_api_product = fields.Char('API Product', readonly=True)
    jetcheckout_api_hash = fields.Char('API Hash', readonly=True)
    jetcheckout_api_tx = fields.Integer('API TransactionID', readonly=True)
    jetcheckout_api_return_url = fields.Char('API Return URL', readonly=True)
