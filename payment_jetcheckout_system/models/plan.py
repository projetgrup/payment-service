# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentPlan(models.Model):
    _name = 'payment.plan'
    _description = 'Payment Plans'
    _order = 'id desc'

    def _compute_name(self):
        for payment in self:
            payment.name = payment.partner_id.name

    name = fields.Char(compute='_compute_name')
    item_id = fields.Many2one('payment.item', ondelete='restrict', readonly=True)
    partner_id = fields.Many2one('res.partner', ondelete='restrict', related='item_id.parent_id', readonly=True)
    token_id = fields.Many2one('payment.token', ondelete='restrict', readonly=True)
    amount = fields.Monetary(readonly=True)
    date = fields.Date(readonly=True)
    paid = fields.Boolean(readonly=True)
    paid_date = fields.Datetime(readonly=True)
    installment_count = fields.Integer(readonly=True)
    transaction_ids = fields.Many2many('payment.transaction', 'transaction_plan_rel', 'plan_id', 'transaction_id', string='Transactions', readonly=True)
    system = fields.Selection(related='item_id.system', readonly=True)
    company_id = fields.Many2one(related='item_id.company_id', readonly=True)
    currency_id = fields.Many2one(related='item_id.currency_id', readonly=True)

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


class PaymentPlanWizard(models.TransientModel):
    _name = 'payment.plan.wizard'
    _description = 'Payment Plan Wizard'

    item_ids = fields.Many2many('payment.item', 'item_plan_wizard_rel', 'wizard_id', 'item_id', string='Items', readonly=True)
