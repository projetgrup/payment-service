# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    system = fields.Selection(selection_add=[('oco', 'Order Checkout')])
    amount_confirmed = fields.Float('Confirmed Amount')

    def system_oco_update_amount_confirmed(self):
        wizard = self.env['payment.oco.sale.order.amount'].create({
            'order_id': self.id,
            'amount': self.amount_confirmed,
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

    def confirm(self):
        self.order_id.amount_confirmed = self.amount
