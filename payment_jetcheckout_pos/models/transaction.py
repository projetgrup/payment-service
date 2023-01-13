# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    pos_order_id = fields.Many2one('pos.order', string='PoS Order', copy=False, readonly=True)
    pos_order_name = fields.Char(string='PoS Order Name', copy=False, readonly=True)
    pos_method_id = fields.Many2one('pos.payment.method', string='PoS Payment Method', copy=False, readonly=True)
