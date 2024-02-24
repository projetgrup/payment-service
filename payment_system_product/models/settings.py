# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    system_product = fields.Boolean(related='company_id.system_product', readonly=False)
