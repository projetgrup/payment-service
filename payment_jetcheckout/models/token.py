# -*- coding: utf-8 -*-
import uuid
from odoo import fields, models, api, _
#from odoo.exceptions import UserError


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

    @api.model
    def create(self, values):
        res = super().create(values)
        res['jetcheckout_card_token'] = str(uuid.uuid4())
        return res

    #def unlink(self):
    #    for token in self:
    #        if token.transaction_ids:
    #            raise UserError(_('Token "%s" cannot be deleted because of it has been used in a transaction.'))
    #    return super().unlink()
