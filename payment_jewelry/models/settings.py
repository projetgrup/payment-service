# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    jewelry_payment_validity_ok = fields.Boolean(related='company_id.jewelry_payment_validity_ok', readonly=False)
    jewelry_payment_validity_time = fields.Integer(related='company_id.jewelry_payment_validity_time', readonly=False)
