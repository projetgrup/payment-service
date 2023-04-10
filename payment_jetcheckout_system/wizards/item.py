# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentItemWizard(models.TransientModel):
    _name = 'payment.item.wizard'
    _description = 'Payment Items Wizard'

    partner_id = fields.Many2one('res.partner', readonly=True)
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
        return {
            'name': 'Payment Items',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/p/%s' % self.partner_id._get_token()
        }
