# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    system = fields.Selection(selection_add=[('supplier', 'Supplier Payment System')])
    limit_card = fields.Float(string='Credit Card Limit')
    limit_tx = fields.Float(string='Transaction Based Limit')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.company.system == 'supplier':
            res['system'] = 'supplier'
            res['company_id'] = self.env.company.id
            res['partner_id'] = self.env.company.partner_id.id
            res['acquirer_id'] = self.acquirer_id._get_acquirer(company=self.env.company, providers=['jetcheckout'], limit=1).id
            res['acquirer_ref'] = '-'
        return res

    def action_verify(self):
        if self.verified:
            return

        action = self.env.ref('payment_supplier.action_token_verify').sudo().read()[0]
        action['context'] = {'default_data': json.dumps({'id': self.id, 'name': self.name})}
        return action


class PaymentTokenVerify(models.TransientModel):
    _name = 'payment.token.verify'
    _description = 'Payment Token Verify'

    data = fields.Char(readonly=True)
