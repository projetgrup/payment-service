# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    pos_order_id = fields.Many2one('pos.order', string='PoS Order', readonly=True)
    pos_order_name = fields.Char(string='PoS Order Name', readonly=True)
    pos_method_id = fields.Many2one('pos.payment.method', string='PoS Payment Method', readonly=True)
    pos_payment_id = fields.Many2one('pos.payment', string='PoS Payment', readonly=True)
