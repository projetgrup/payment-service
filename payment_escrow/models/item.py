# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    product_id = fields.Many2one('product.product', string='Product', domain=[('system', '=', 'escrow')])