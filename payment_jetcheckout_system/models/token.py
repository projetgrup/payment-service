# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    system = fields.Selection(selection=[], readonly=True, default=lambda self: self.env.company.system)
