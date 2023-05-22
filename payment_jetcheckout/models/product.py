# -*- coding: utf-8 -*-
from odoo import models


class Product(models.Model):
    _inherit = 'product.product'

    def _sanitize_vals(self, vals):
        super(Product, self)._sanitize_vals(vals)
        if 'base_unit_count' in self._fields and 'base_unit_count' not in vals:
            vals['base_unit_count'] = 0
