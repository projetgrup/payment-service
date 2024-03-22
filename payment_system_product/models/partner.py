# -*- coding: utf-8 -*-
from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    payment_product_attribute_ids = fields.One2many('payment.product.partner', 'partner_id', 'Product Attributes')
    payment_product_categ_ids = fields.Many2many('product.category', 'payment_product_categ_partner_rel', 'partner_id', 'categ_id', 'Product Categories')
