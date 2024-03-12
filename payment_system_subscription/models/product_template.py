# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    payment_recurring_invoice = fields.Boolean('Subscription Product', help='If set, confirming a sale order with this product will create a subscription')
    payment_subscription_template_id = fields.Many2one('payment.subscription.template', 'Subscription Template', help='Product will be included in a selected template')

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        if 'payment_subscription_template_id' in values:
            for product in self.product_variant_ids:
                    product.payment_subscription_template_id = values['payment_subscription_template_id']
        return res

    @api.model
    def create(self, values):
        res = super(ProductTemplate, self).create(values)
        for product in res.product_variant_ids:
            product.payment_subscription_template_id = res.payment_subscription_template_id.id
        return res
