# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class PaymentItemWizard(models.TransientModel):
    _name = 'payment.item.wizard'
    _description = 'Payment Items Wizard'

    partner_id = fields.Many2one('res.partner', readonly=True)
    url = fields.Char(readonly=True)
    line_ids = fields.One2many('payment.item', related='partner_id.payable_ids', readonly=False)

    def write(self, values):
        res = super().write(values)
        if 'line_ids' in values:
            item = self.env['payment.item']
            for line in values['line_ids']:
                if line[0] == 0:
                    item.create(line[2])
                elif line[0] == 1:
                    item.write(line[2])
                elif line[0] == 2:
                    item.browse(line[1]).unlink()
        return res

    def confirm(self):
        currency = self.line_ids.mapped('currency_id')
        if len(currency) > 1:
            raise UserError(_('Payment items must share one common currency'))

        return {
            'name': 'Payment Items',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '%s/p/%s' % (self.get_base_url(), self.partner_id._get_token())
        }
    
    def send(self):
        return self.partner_id.action_send()
