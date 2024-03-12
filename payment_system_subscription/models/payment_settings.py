# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    system_subscription = fields.Boolean(related='company_id.system_subscription', readonly=False)

    @api.onchange('system_subscription')
    def onchange_system_subscription(self):
        if self.system_subscription:
            self.system_product = True
