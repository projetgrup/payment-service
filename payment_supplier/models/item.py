# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    system = fields.Selection(selection_add=[('supplier', 'Supplier Payment System')])

    def action_plan(self):
        action = self.env.ref('payment_supplier.action_plan_wizard').sudo().read()[0]
        action['context'] = {'default_item_ids': [(6, 0, self.ids)]}
        return action
