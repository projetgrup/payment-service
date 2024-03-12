# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PaymentSubscriptionSnapshot(models.Model):
    _name = 'payment.subscription.snapshot'
    _description = 'Payment Subscription Snapshot'

    subscription_id = fields.Many2one('payment.subscription', string='Subscription', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    recurring_monthly = fields.Float(string='Monthly Recurring Revenue', required=True)
