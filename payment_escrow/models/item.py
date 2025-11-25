# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    ad_id = fields.Many2one('escrow.ad', string='Advertisement', domain=[('state', '=', 'new')])
    product_id = fields.Many2one('product.product', string='Product')

    @api.model
    def create(self, vals):
        res = super(PaymentItem, self).create(vals)
        if res.system == 'escrow' and res.ad_id:
            res.ad_id.write({'sale_state': 'waiting_payment'})
        return res

    @api.depends('residual_amount')
    def _compute_paid(self):
        super()._compute_paid()
        for item in self.filtered(lambda x: x.system == 'escrow'):
            if item.paid and item.ad_id and item.ad_id.sale_state != 'waiting_official_doc':
                item.ad_id.write({'sale_state': 'waiting_official_doc'})