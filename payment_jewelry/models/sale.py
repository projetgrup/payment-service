# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])
