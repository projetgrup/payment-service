# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    def _compute_bank_verified(self):
        for item in self:
            item.system_supplier_bank_verified = any(item.parent_id.bank_ids.mapped('api_state'))

    system = fields.Selection(selection_add=[('supplier', 'Supplier Payment System')])
    system_supplier_bank_verified = fields.Boolean(compute='_compute_bank_verified')

    def action_plan(self):
        action = self.env.ref('payment_jetcheckout_system.action_plan_wizard').sudo().read()[0]
        item_ids = self.filtered(lambda item: any(bank.api_state for bank in item.parent_id.bank_ids))
        action['context'] = {'default_item_ids': [(6, 0, item_ids.ids)]}
        return action
