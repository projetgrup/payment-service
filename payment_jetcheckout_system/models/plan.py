# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError


class PaymentPlan(models.Model):
    _name = 'payment.plan'
    _description = 'Payment Plans'
    _order = 'date desc'

    def _compute_name(self):
        for payment in self:
            payment.name = payment.partner_id.name

    name = fields.Char(compute='_compute_name')
    item_id = fields.Many2one('payment.item', ondelete='restrict', readonly=True)
    partner_id = fields.Many2one('res.partner', ondelete='restrict', readonly=True)
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

    @api.depends('item_ids')
    def _compute_desc(self):
        for wizard in self:
            count = len(wizard.item_ids)
            currency = self.env.company.currency_id
            amount = formatLang(self.env, sum(wizard.item_ids.mapped('amount')), currency_obj=currency)
            wizard.desc = _('<strong class="text-primary">%s</strong> partner(s) selected. Total amount is <strong class="text-primary">%s</strong>.' % (count, amount))

    item_ids = fields.Many2many('payment.item', 'item_plan_wizard_rel', 'wizard_id', 'item_id', string='Items', readonly=True)
    desc = fields.Html(sanitize=False, compute='_compute_desc')
    line_ids = fields.One2many('payment.plan.wizard.line', 'wizard_id', string='Lines')

    def action_confirm(self):
        for item in self.item_ids:
            amount = item.amount
            values = []
            for line in self.line_ids:
                limit_card = line.token_limit_card
                while limit_card > 0:
                    limit_tx = amount if line.token_limit_tx > amount else line.token_limit_tx
                    values.append({
                        'item_id': item.id,
                        'partner_id': item.parent_id.id,
                        'token_id': line.token_id.id,
                        'amount': limit_tx,
                        'date': item.date,
                    })
                    limit_card -= limit_tx
                    amount -= limit_tx
                    if not amount > 0:
                        break
                if not amount > 0:
                    break

        plans = self.env['payment.plan'].create(values)
        action = self.env.ref('payment_jetcheckout_system.action_plan').read()[0]
        action['domain'] = [('id', 'in', plans.ids)]
        return action


class PaymentPlanWizardLine(models.TransientModel):
    _name = 'payment.plan.wizard.line'
    _description = 'Payment Plan Wizard Line'

    wizard_id = fields.Many2one('payment.plan.wizard')
    token_id = fields.Many2one('payment.token', string='Credit Card', domain=[('verified', '=', True)], required=True)
    token_limit_card = fields.Float(string='Card Limit')
    token_limit_tx = fields.Float(string='Transaction Limit')

    @api.constrains('token_limit_tx')
    def check_token_limit_tx(self):
        for line in self:
            if not line.token_limit_tx > 0:
                raise UserError(_('Transaction limit must be higher than zero!'))

    @api.onchange('token_id')
    def onchange_token_id(self):
        self.token_limit_card = self.token_id.jetcheckout_limit_card if self.token_id else 0
        self.token_limit_tx = self.token_id.jetcheckout_limit_tx if self.token_id else 0
