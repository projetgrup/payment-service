# -*- coding: utf-8 -*-
from odoo import fields, models

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    jetcheckout_api_contact = fields.Char('API Contact', readonly=True)
    jetcheckout_api_order = fields.Char('API Order', readonly=True)
    jetcheckout_api_product = fields.Char('API Product', readonly=True)
    jetcheckout_api_hash = fields.Char('API Hash', readonly=True)
    jetcheckout_api_id = fields.Integer('API TransactionID', readonly=True)
    jetcheckout_api_card_return_url = fields.Char('API Card Return URL', readonly=True)
    jetcheckout_api_bank_return_url = fields.Char('API Bank Return URL', readonly=True)
    jetcheckout_api_bank_webhook_url = fields.Char('API Bank Webhook URL', readonly=True)
