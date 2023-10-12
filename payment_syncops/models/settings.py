# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    syncops_payment_page_partner_required = fields.Boolean(related='company_id.syncops_payment_page_partner_required', readonly=False)
