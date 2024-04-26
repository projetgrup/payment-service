# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('price_subtotal', 'payment_subscription_start_date', 'payment_subscription_end_date')
    def _compute_mrr(self):
        for line in self:
            if not (line.payment_subscription_end_date and line.payment_subscription_start_date):
                line.payment_subscription_mrr = 0
                continue

            delta = relativedelta(
                dt1=line.payment_subscription_end_date + relativedelta(days=1),
                dt2=line.payment_subscription_start_date,
            )
            months = delta.months + delta.days / 30.0 + delta.years * 12.0
            line.payment_subscription_mrr = line.price_subtotal / months if months else 0

    payment_subscription_id = fields.Many2one('payment.subscription')
    payment_subscription_start_date = fields.Date(string='Subscription Revenue Start Date', readonly=True)
    payment_subscription_end_date = fields.Date(string='Subscription Revenue End Date', readonly=True)
    payment_subscription_mrr = fields.Monetary(
        string='Monthly Recurring Revenue',
        compute='_compute_mrr',
        help='The MRR is computed by dividing the signed amount (in company currency) by the '
        'amount of time between the start and end dates converted in months.\nThis allows '
        'comparison of invoice lines created by subscriptions with different temporalities.\n'
        'The computation assumes that 1 month is comprised of exactly 30 days, regardless '
        ' of the actual length of the month.',
    )
