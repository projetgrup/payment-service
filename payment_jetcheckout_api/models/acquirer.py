# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    def _get_branch_line_domain(self, line, tx):
        res = super()._get_branch_line_domain(line, tx)
        if tx.jetcheckout_payment_type == 'physicalpos':
            method = fields.first(tx.paylox_api_method_ids.filtered(lambda m: m.type == 'physicalpos'))
            if method and method.type_physicalpos_ids:
                res.append(('method_physicalpos_ids', 'in', method.type_physicalpos_ids.ids))
        return res
