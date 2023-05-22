# -*- coding: utf-8 -*-
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _sanitize_vals(self, vals):
        super(ProductTemplate, self)._sanitize_vals(vals)
        if 'base_unit_count' in self._fields and ('base_unit_count' not in vals or not vals['base_unit_count']):
            vals['base_unit_count'] = 0
