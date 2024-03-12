# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.depends('state')
    def _compute_payment_renewal_allowed(self):
        for tx in self:
            tx.payment_renewal_allowed = self.state in ['done', 'authorized']

    payment_renewal_allowed = fields.Boolean(compute='_compute_payment_renewal_allowed', store=False, help='Technical field used to control the renewal flow based on the transaction\'s state.')
