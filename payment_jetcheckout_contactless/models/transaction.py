# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    paylox_contactless_ok = fields.Boolean('Paylox Contactless Payment')
