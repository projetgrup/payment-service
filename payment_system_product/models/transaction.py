# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    paylox_product_ids = fields.One2many('payment.transaction.product', 'transaction_id', 'Products')


class PaymentTransactionProduct(models.Model):
    _name = 'payment.transaction.product'
    _description = 'Payment Transaction Product'

    transaction_id = fields.Many2one('payment.transaction', ondelete='cascade')
    product_id = fields.Many2one('product.product')
    quantity = fields.Float()
