# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentPage(models.Model):
    _name = 'payment.page'
    _description = 'Payment Pages'

    name = fields.Char(translate=True)
    path = fields.Char()
