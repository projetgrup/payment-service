# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    system = fields.Selection(selection=[], readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.company.system:
            for vals in vals_list:
                vals['system'] = self.env.company.system
                vals['company_id'] = self.env.company.id
        return super().create(vals_list)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    paylox_system_price_unit = fields.Monetary()
