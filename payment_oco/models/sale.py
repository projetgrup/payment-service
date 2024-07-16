# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    system = fields.Selection(selection_add=[('oco', 'Order Checkout')])

    def system_oco_update_amount_approved(self):
        wizard = self.env['payment.oco.sale.order.amount'].create({
            'order_id': self.id,
            'amount': self.amount_approved,
        })
        action = self.env.ref('payment_oco.action_order_amount').sudo().read()[0]
        action['res_id'] = wizard.id
        action['context'] = {'dialog_size': 'small', 'create': False, 'delete': False}
        return action


class PaymentOcoSaleOrderAmount(models.Model):
    _name = 'payment.oco.sale.order.amount'
    _description = 'Payment Order Checkout Sale Order Amount'

    order_id = fields.Many2one('sale.order')
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id')
    amount = fields.Monetary()

    def approve(self):
        txs = self.order_id.transaction_ids.filtered(lambda tx: tx.state == 'authorized')
        captured = False
        for tx in txs:
            if captured:
                tx.action_cancel()
            else:
                tx.with_context(amount=self.amount).action_capture()

        self.order_id.amount_approved = self.amount
