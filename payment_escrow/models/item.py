# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    product_id = fields.Many2one('product.product', string='Product', domain=[('system', '=', 'escrow')])
    system_escrow_ad_id = fields.Many2one('payment.escrow.ad')

    @api.depends('residual_amount')
    def _compute_paid(self):
        super()._compute_paid()
        for item in self.filtered(lambda x: x.system == 'escrow'):
            if item.paid and item.product_id and item.product_id.escrow_state != 'waiting_official_sale_img':
                item.product_id.write({'escrow_state': 'waiting_official_sale_img'})