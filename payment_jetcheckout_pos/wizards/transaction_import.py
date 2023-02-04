# -*- coding: utf-8 -*-
from odoo import fields, models


class PaymentTransactionImport(models.TransientModel):
    _inherit= 'payment.transaction.import'

    def _get_row(self, value):
        res = super()._get_row(value)
        res.update({
            'pos_method_id': self.env['pos.payment.method'].search([('name', '=', value['PoS Payment Method'])], limit=1).id
        })
        return res

    def _prepare_row(self, reference, line):
        res = super()._prepare_row(reference, line)
        res.update({
            'pos_method_id': line.pos_method_id.id
        })
        return res


class PaymentTransactionImportLine(models.TransientModel):
    _inherit = 'payment.transaction.import.line'

    pos_method_id = fields.Many2one('pos.payment.method', string='PoS Payment Method', readonly=True)
