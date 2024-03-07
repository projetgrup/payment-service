# -*- coding: utf-8 -*-
from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    payment_product_attribute_ids = fields.One2many('payment.product.partner', 'partner_id', 'Product Attributes')
