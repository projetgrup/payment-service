# -*- coding: utf-8 -*-
from odoo import models


class PaymentPlan(models.Model):
    _inherit = 'payment.plan'

    def write(self, values):
        res = super().write(values)
        if 'approval_state' in values and values['approval_state'] == '+':
            for tx in self.mapped('transaction_ids'):
                if tx.jetcheckout_connector_ok:
                    tx.with_context(no_button=True, plan_approved=True).action_process_connector()
            for item in self.mapped('item_id'):
                item.action_process_connector()
        return res
