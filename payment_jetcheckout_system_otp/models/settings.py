# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    otp_redirect_url = fields.Char(related='company_id.otp_redirect_url', readonly=False)
