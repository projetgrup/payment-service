# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    system_product = fields.Boolean(related='company_id.system_product', readonly=False)
    system_product_payment_validity_ok = fields.Boolean(related='company_id.system_product_payment_validity_ok', readonly=False)
    system_product_payment_validity_time = fields.Integer(related='company_id.system_product_payment_validity_time', readonly=False)
