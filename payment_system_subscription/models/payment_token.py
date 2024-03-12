# -*- coding: utf-8 -*-
from odoo import models


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    def get_linked_records(self):
        res = super(PaymentToken, self).get_linked_records()
        for token in self:
            subs = self.env['payment.subscription'].search([('payment_token_id', '=', token.id)])
            for sub in subs:
                res[token.id].append({
                    'description': subs._description,
                    'id': sub.id,
                    'name': sub.name,
                    'url': '/my/subscriptions/' + str(sub.id) + '/' + str(sub.uuid)
                })
        return res
