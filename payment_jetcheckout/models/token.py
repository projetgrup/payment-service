# -*- coding: utf-8 -*-
from odoo import fields, models, _

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    jetcheckout_card_userkey = fields.Char('Credit Card User Key')
    jetcheckout_card_token = fields.Char('Credit Card Token')
    jetcheckout_card_number = fields.Char('Credit Card Number')
    jetcheckout_card_holder = fields.Char('Credit Card Holder')
    jetcheckout_card_expiry_month = fields.Char('Credit Card Expiry Month')
    jetcheckout_card_expiry_year = fields.Char('Credit Card Expiry Year')
    jetcheckout_card_cvc = fields.Char('Credit Card CVC')
    jetcheckout_card_installment = fields.Char('Credit Card Installment')
    jetcheckout_card_3d = fields.Boolean('Credit Card 3D')
    jetcheckout_card_save = fields.Boolean('Credit Card Save')
