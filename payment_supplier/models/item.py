# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    @api.depends('parent_id.bank_ids.api_state')
    def _compute_bank_verified(self):
        for item in self:
            if item.system == 'supplier':
                item.system_supplier_bank_verified = any(item.parent_id.bank_ids.mapped('api_state'))
            else:
                item.system_supplier_bank_verified = False

    system = fields.Selection(selection_add=[('supplier', 'Supplier Payment System')])
    system_supplier_bank_verified = fields.Boolean(compute='_compute_bank_verified', store=True, readonly=True)
    system_supplier_plan_mail_sent = fields.Boolean(readonly=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.company.system == 'supplier':
            res['mail_ok'] = True
        return res
 