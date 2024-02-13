# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    jewelry_payment_validity = fields.Integer(related='company_id.jewelry_payment_validity', readonly=False)
