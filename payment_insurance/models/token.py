# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    system = fields.Selection(selection_add=[('insurance', 'Insurance Payment System')])
