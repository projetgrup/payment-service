# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    system = fields.Selection(selection_add=[('vendor', 'Vendor Payment System')])
