# -*- coding: utf-8 -*-
from odoo import fields, models

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    partner_authorized = fields.Char('Partner Authorized', readonly=True)
    jetcheckout_page_product_name = fields.Char('Page Product', readonly=True)
    jetcheckout_page_hash = fields.Char('Page Hash', readonly=True)
    jetcheckout_page_tx = fields.Integer('Page Transaction', readonly=True)
    jetcheckout_page_return_url = fields.Char('Page Return URL', readonly=True)
