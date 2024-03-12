# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    payment_subscription_template_id = fields.Many2one('payment.subscription.template', 'Subscription Template', help='Product will be included in a selected template')
