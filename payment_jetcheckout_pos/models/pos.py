# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_vpos = fields.Boolean(string='Virtual PoS', copy=False)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _compute_transaction_count(self):
        for order in self:
            order.transaction_count = len(order.transaction_ids)

    transaction_ids = fields.One2many('payment.transaction', 'pos_order_id', string='Transactions', copy=False)
    transaction_count = fields.Integer(compute='_compute_transaction_count')

    @api.model
    def _process_order(self, order, draft, existing_order):
        res = super()._process_order(order, draft, existing_order)
        pos_order = self.browse(res)
        transaction_ids =  order['data']['transaction_ids']
        if transaction_ids:
            pos_order.transaction_ids = [(6, 0, transaction_ids)]
        return res

    def action_view_transactions(self):
        self.ensure_one()
        action = self.env.ref('payment.action_payment_transaction').read()[0]
        action['domain'] = [('pos_order_id', '=', self.id)]
        return action
