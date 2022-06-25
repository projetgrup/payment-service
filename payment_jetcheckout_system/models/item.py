# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PaymentItem(models.Model):
    _name = 'payment.item'
    _description = 'Payment Items'
    _order = 'id desc'

    def _compute_name(self):
        for payment in self:
            payment.name = payment.parent_id.name

    @api.onchange('child_id')
    def _onchange_child_id(self):
        self.parent_id = self.child_id.parent_id.id if self.child_id else False

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        self.child_id = self.parent_id.child_ids and self.parent_id.child_ids[0].id if self.parent_id else False

    name = fields.Char(compute='_compute_name')
    child_id = fields.Many2one('res.partner', ondelete='restrict')
    parent_id = fields.Many2one('res.partner', ondelete='restrict')
    amount = fields.Monetary()
    paid = fields.Boolean(readonly=True)
    paid_amount = fields.Monetary(readonly=True)
    installment_count = fields.Integer(readonly=True)
    paid_date = fields.Datetime(readonly=True)
    transaction_ids = fields.Many2many('payment.transaction', 'transaction_item_rel', 'item_id', 'transaction_id', string='Transactions')
    system = fields.Selection(related='company_id.system', store=True, readonly=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, readonly=True)

    def onchange(self, values, field_name, field_onchange):
        return super(PaymentItem, self.with_context(recursive_onchanges=False)).onchange(values, field_name, field_onchange)

    def action_transaction(self):
        self.ensure_one()
        action = self.env.ref('payment.action_payment_transaction').sudo().read()[0]
        action['domain'] = [('id', 'in', self.transaction_ids.ids)]
        action['context'] = {'create': False, 'edit': False, 'delete': False}
        return action

    def action_receipt(self):
        self.ensure_one()
        transaction_ids = self.transaction_ids.filtered(lambda x: x.state == 'done')
        action = self.env.ref('payment_jetcheckout.report_receipt').report_action(transaction_ids.ids)
        return action

    def action_conveyance(self):
        self.ensure_one()
        transaction_ids = self.transaction_ids.filtered(lambda x: x.state == 'done')
        action = self.env.ref('payment_jetcheckout.report_conveyance').report_action(transaction_ids.ids)
        return action
