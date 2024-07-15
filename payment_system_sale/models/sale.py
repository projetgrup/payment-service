# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    system = fields.Selection(selection=[], readonly=True)

    @api.constrains('company_id', 'order_line')
    def _check_order_line_company_id(self):
        if self.system == 'oco':
            return
        return super()._check_order_line_company_id()

    @api.model_create_multi
    def create(self, vals_list):
        company = self.env.company
        if company.parent_id:
            company = company.parent_id
        if company.system:
            for vals in vals_list:
                vals['system'] = company.system
                #vals['company_id'] = company.id # It was closed because of OCO
        return super().create(vals_list)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    paylox_system_price_unit = fields.Monetary()
    product_id = fields.Many2one('product.product', check_company=False)
