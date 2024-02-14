# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    system = fields.Selection(selection=[], readonly=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    paylox_system_price_unit = fields.Monetary()
