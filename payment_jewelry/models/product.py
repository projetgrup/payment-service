# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])


class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])
    payment_type = fields.Selection(selection_add=[('weight', 'Weight')])
