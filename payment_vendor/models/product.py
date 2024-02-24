# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('vendor', 'Vendor Payment System')])


class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('vendor', 'Vendor Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('vendor', 'Vendor Payment System')])
