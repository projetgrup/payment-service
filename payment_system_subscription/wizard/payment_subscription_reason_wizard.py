# -*- coding: utf-8 -*-
from odoo import fields, models


class PaymentSubscriptionCloseReasonWizard(models.TransientModel):
    _name = 'payment.subscription.reason.wizard'
    _description = 'Subscription Reason Wizard'

    reason_id = fields.Many2one('payment.subscription.reason', string='Reason')

    def confirm(self):
        self.ensure_one()
        subscription = self.env['payment.subscription'].browse(self.env.context.get('active_id'))
        subscription.reason_id = self.reason_id
        subscription.set_close()
