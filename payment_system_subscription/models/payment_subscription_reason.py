# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PaymentSubscriptionReason(models.Model):
    _name = 'saas.subscription.reason'
    _description = 'Subscription Close Reason'
    _order = 'sequence, id'

    name = fields.Char('Reason', required=True, translate=True)
    sequence = fields.Integer(default=10)
