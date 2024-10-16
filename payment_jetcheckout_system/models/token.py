# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    system = fields.Selection(selection=[], readonly=True, default=lambda self: self.env.company.system)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.company.system:
            res['system'] = self.env.company.system
            res['company_id'] = self.env.company.id
            res['partner_id'] = self.env.company.partner_id.id
            res['acquirer_id'] = self.acquirer_id._get_acquirer(company=self.env.company, providers=['jetcheckout'], limit=1).id
            res['acquirer_ref'] = '-'
        return res

    def action_verify(self):
        if self.verified:
            return

        action = self.env.ref('payment_jetcheckout_system.action_token_verify').sudo().read()[0]
        action['context'] = {'default_data': json.dumps({'id': self.id, 'name': self.name})}
        return action


class PaymentTokenVerify(models.TransientModel):
    _name = 'payment.token.verify'
    _description = 'Payment Token Verify'

    data = fields.Char(readonly=True)
