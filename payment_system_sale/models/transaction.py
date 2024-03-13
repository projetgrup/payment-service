# -*- coding: utf-8 -*-
from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _paylox_done_postprocess(self):
        res = super()._paylox_done_postprocess()
        products = self.env['payment.transaction.product'].sudo().search([('transaction_id', '=', self.id)])
        if products:
            order = self.env['sale.order'].sudo().create({
                'company_id': self.company_id.id,
                'system': self.company_id.system,
                'partner_id': self.partner_id.id,
                'order_line': [(0, 0, {
                    'product_id': product.product_id.id,
                    'product_uom_qty': product.quantity,
                }) for product in products]
            })
            self.sale_order_ids = [(6, 0, order.ids)]
        return res
