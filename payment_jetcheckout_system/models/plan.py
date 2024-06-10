# -*- coding: utf-8 -*-
import json
import requests

from odoo import models, fields, api, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError


class PaymentPlan(models.Model):
    _name = 'payment.plan'
    _description = 'Payment Plans'
    _order = 'date desc, id'

    def _compute_name(self):
        for payment in self:
            payment.name = payment.partner_id.name

    @api.depends('paid', 'message')    
    def _compute_result(self):
        for plan in self:
            if plan.paid and plan.message:
                plan.result = '<i class="fa fa-check text-primary" title="%s"/>' % plan.message
            elif plan.message:
                plan.result = '<i class="fa fa-times text-danger" title="%s"/>' % plan.message
            else:
                #plan.result = '<i class="fa fa-minus text-muted" title="%s"/>' % _('No message yet')
                plan.result = ''

    name = fields.Char(compute='_compute_name')
    item_id = fields.Many2one('payment.item', ondelete='restrict', readonly=True)
    partner_id = fields.Many2one('res.partner', ondelete='restrict', readonly=True)
    token_id = fields.Many2one('payment.token', ondelete='restrict', readonly=True, string='Credit Card')
    amount = fields.Monetary(readonly=True)
    date = fields.Date(readonly=True)
    message = fields.Char(readonly=True)
    result = fields.Html(sanitize=False, readonly=True, compute='_compute_result')
    paid = fields.Boolean(readonly=True)
    paid_date = fields.Datetime(readonly=True)
    installment_count = fields.Integer(readonly=True, default=1)
    transaction_ids = fields.Many2many('payment.transaction', 'transaction_plan_rel', 'plan_id', 'transaction_id', string='Transactions', readonly=True)
    system = fields.Selection(related='item_id.system', readonly=True)
    company_id = fields.Many2one(related='item_id.company_id', readonly=True)
    currency_id = fields.Many2one(related='item_id.currency_id', readonly=True)
    approval_state = fields.Selection([
        ('+', 'Approved'),
        ('-', 'Disapproved'),
    ], readonly=True)
    approval_result = fields.Char(readonly=True)

    def payment(self):
        company = self.partner_id.company_id or self.env.company
        acquirer = self.env['payment.acquirer'].sudo()._get_acquirer(company=company, providers=['jetcheckout'], limit=1, raise_exception=False)
        if not acquirer:
            self.message = _('No acquirer found')
            return

        website = self.env['website'].sudo().search([('company_id', '=', company.id)])
        if not website:
            self.message = _('No website found')
            return

        if self.installment_count < 1:
            self.installment_count = 1
        installment = self.installment_count

        url = '%s/payment/init' % website.domain
        data = {
            'type': 'virtual_pos',
            'card': {
                'type': self.token_id.jetcheckout_type or '',
                'family': self.token_id.jetcheckout_family or '',
                'code': self.token_id.jetcheckout_security or '',
                'date': self.token_id.jetcheckout_expiry or '',
                'holder': self.token_id.jetcheckout_holder or '',
                'token': self.token_id.id or 0,
            },
            'amount': self.amount,
            'partner': self.partner_id.id,
            'currency': self.currency_id.id,
            'installment': {
                'id': installment,
                'index': 0,
                'rows': [{
                    'id': installment,
                    'count': installment,
                    'plus': 0,
                    'irate': 0.0,
                    'crate': 0.0,
                    'corate': 0.0,
                    'idesc': _('%s Installment') if installment > 1 else _('Single Payment') % installment,
                }],
            },
            'campaign': '',
        }

        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json().get('result', {})
            if result.get('response_code') == '00':
                self.message = _('Success')
            else:
                self.message = result.get('message') or result.get('error') or _('An error occured')
        else:
            self.message = response.reason

    def approve(self):
        if self.approval_state == '+':
            return

        transactions = self.transaction_ids.filtered(lambda tx: tx.state == 'done')
        if not transactions:
            return

        transaction = transactions[0]
        url = '%s/api/v1/payment/submerchant/approve' % transaction.acquirer_id._get_paylox_api_url()
        data = {
            "application_key": transaction.acquirer_id.jetcheckout_api_key,
            "transaction_id": transaction.jetcheckout_transaction_id,
            "language": "tr",
        }

        response = requests.post(url, data=json.dumps(data))
        try:
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == "00":
                    self.approval_state = '+'
                    self.approval_result = _('Approved')
                else:
                    self.approval_result = _('%s (Error Code: %s)') % (result['message'], result['response_code'])
            else:
                self.approval_result = _('%s (Error Code: %s)') % (response.reason, response.status_code)
            self.env.cr.commit()
        except:
            self.env.cr.rollback()

    def disapprove(self):
        if self.approval_state == '-':
            return

        transactions = self.transaction_ids.filtered(lambda tx: tx.state == 'done')
        if not transactions:
            return

        transaction = transactions[0]
        url = '%s/api/v1/payment/submerchant/disapprove' % transaction.acquirer_id._get_paylox_api_url()
        data = {
            "application_key": transaction.acquirer_id.jetcheckout_api_key,
            "transaction_id": transaction.jetcheckout_transaction_id,
            "language": "tr",
        }

        response = requests.post(url, data=json.dumps(data))
        try:
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == "00":
                    self.approval_state = '-'
                    self.approval_result = _('Disapproved')
                else:
                    self.approval_result = _('%s (Error Code: %s)') % (result['message'], result['response_code'])
            else:
                self.approval_result = _('%s (Error Code: %s)') % (response.reason, response.status_code)
            self.env.cr.commit()
        except:
            self.env.cr.rollback()

    def action_payment(self):
        for plan in self:
            plan.payment()

    def action_approve(self):
        for plan in self:
            plan.approve()

    def action_disapprove(self):
        for plan in self:
            plan.disapprove()

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
        action = self.env.ref('payment_jetcheckout_system.action_plan').sudo().read()[0]
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
