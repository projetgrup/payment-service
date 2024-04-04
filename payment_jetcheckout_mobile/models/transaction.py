# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    paylox_contactless_ok = fields.Boolean('Paylox Contactless Payment')

    def _paylox_query(self, values={}):
        self.ensure_one()
        if self.paylox_contactless_ok:
            return
        return super(PaymentTransaction, self)._paylox_query(values=values)
