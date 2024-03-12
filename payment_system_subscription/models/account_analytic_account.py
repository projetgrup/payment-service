# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    def _compute_payment_subscription_count(self):
        payment_subscription_data = self.env['payment.subscription'].read_group(
            domain=[('analytic_account_id', 'in', self.ids)],
            fields=['analytic_account_id'],
            groupby=['analytic_account_id'],
        )

        data = dict([(m['analytic_account_id'][0], m['analytic_account_id_count']) for m in payment_subscription_data])
        for account in self:
            account.payment_subscription_count = data.get(account.id, 0)

    payment_subscription_ids = fields.One2many('payment.subscription', 'analytic_account_id', string='Subscriptions')
    payment_subscription_count = fields.Integer(compute='_compute_payment_subscription_count', string='Subscription Count')

    def action_payment_subscriptions(self):
        payment_subscription_ids = self.mapped('payment_subscription_ids').ids
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'payment.subscription',
            'views': [[False, 'tree'], [False, 'form']],
            'domain': [['id', 'in', payment_subscription_ids]],
            'context': {'create': False},
            'name': 'Subscriptions',
        }
        if len(payment_subscription_ids) == 1:
            result['views'] = [(False, 'form')]
            result['res_id'] = payment_subscription_ids[0]
        return result
