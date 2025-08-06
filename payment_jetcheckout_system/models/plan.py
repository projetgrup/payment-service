# -*- coding: utf-8 -*-
import json
import uuid
import base64
import requests
from urllib.parse import urlparse, quote

from odoo import models, fields, api, _
from odoo.http import request
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round


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
            if plan.transaction_state == 'pending':
                plan.result = '<i class="fa fa-circle-o-notch fa-spin text-600" title="%s"/>' % _('Transaction in progress')
            elif plan.paid and plan.message:
                plan.result = '<i class="fa fa-check text-primary" title="%s"/>' % plan.message
            elif plan.message:
                plan.result = '<i class="fa fa-times text-danger" title="%s"/>' % plan.message
            else:
                #plan.result = '<i class="fa fa-minus text-muted" title="%s"/>' % _('No message yet')
                plan.result = ''

    @api.depends('transaction_ids.state')    
    def _compute_paid(self):
        for plan in self:
            state = False
            message = False
            transactions = plan.transaction_ids
            for transaction in transactions:
                if transaction.state == 'done' and not transaction.source_transaction_id:
                    sources = self.env['payment.transaction'].sudo().search([('source_transaction_id', '=', transaction.id)])
                    refund_amount = -sum(sources.mapped('amount'))
                    if not float_compare(refund_amount, transaction.amount, precision_rounding=transaction.currency_id.rounding):
                        continue
                    plan.paid = True
                    plan.paid_date = transaction.last_state_change
                    plan.amount_paid = transaction.jetcheckout_payment_paid
                    plan.amount_cost = transaction.jetcheckout_commission_amount
                    plan.transaction_state = transaction.state
                    plan.message = transaction.state_message
                    break
                if not state:
                    state = transaction.state
                if not message:
                    message = transaction.state_message
            else:
                plan.paid = False
                plan.paid_date = False
                plan.amount_paid = False
                plan.amount_cost = False
                plan.transaction_state = state
                plan.message = message

    @api.depends('approver_level')
    def _compute_approver_state(self):
        for plan in self:
            partner = plan.create_uid
            company = plan.company_id or plan.partner_id.company_id or self.env.company
            if company.payment_plan_approver_ok:
                level = plan.approver_level or 0
                if level >= 0:
                    for line in company.payment_plan_approver_ids:
                        if partner.id in line.partner_ids.ids:
                            level = line.level + 1
                            break
                    line = fields.first(company.payment_plan_approver_ids.filtered(lambda l: l.level > level))
                    if line:
                        plan.approver_state = _('Level %s approval is waiting') % line.level
                    else:
                        plan.approver_state = _('Approval process has been completed')
                else:
                    plan.approver_state = _('Approval process has been completed')
            else:
                plan.approver_state = _('No need to be approved')

    name = fields.Char(compute='_compute_name')
    uid = fields.Char('Unique ID', readonly=True, copy=False, default=lambda self: str(uuid.uuid4()))
    item_id = fields.Many2one('payment.item', ondelete='restrict', readonly=True, domain='[("company_id", "=", company_id)]')
    partner_id = fields.Many2one('res.partner', ondelete='restrict', readonly=True, domain='[("company_id", "=", company_id)]')
    token_id = fields.Many2one('payment.token', ondelete='restrict', readonly=True, string='Credit Card', domain='[("company_id", "=", company_id)]')
    installment_id = fields.Many2one('payment.acquirer.jetcheckout.installment', readonly=True, string='Installment', default=lambda self: self.env.ref('payment_jetcheckout.installment_1'))
    installment_count = fields.Integer(related='installment_id.count', store=True)
    amount = fields.Monetary(readonly=True)
    date = fields.Date(readonly=True)
    result = fields.Html(sanitize=False, readonly=True, compute='_compute_result')
    message = fields.Char(readonly=True, compute='_compute_paid', store=True)
    paid = fields.Boolean(readonly=True, compute='_compute_paid', store=True)
    paid_date = fields.Datetime(readonly=True, compute='_compute_paid', store=True)
    amount_paid = fields.Monetary(readonly=True, compute='_compute_paid', store=True, string='Paid Amount')
    amount_cost = fields.Monetary(readonly=True, compute='_compute_paid', store=True, string='Cost Amount')
    transaction_state = fields.Char(readonly=True, compute='_compute_paid', store=True, string='Transaction State')
    transaction_ids = fields.Many2many('payment.transaction', 'transaction_plan_rel', 'plan_id', 'transaction_id', string='Transactions', readonly=True, ondelete='restrict')
    system = fields.Selection(related='item_id.system', readonly=True, store=True)
    company_id = fields.Many2one(related='item_id.company_id', readonly=True, store=True)
    currency_id = fields.Many2one(related='item_id.currency_id', readonly=True, store=True)
    approval_state = fields.Selection([('+', 'Approved'), ('-', 'Disapproved')], readonly=True)
    approval_result = fields.Char(readonly=True)
    approver_level = fields.Integer(readonly=True)
    approver_state = fields.Char(compute='_compute_approver_state')
    approver_ids = fields.Many2many('res.partner', 'approver_plan_rel', 'plan_id', 'approver_id', string='Approvers', readonly=True)
    disapprover_ids = fields.Many2many('res.partner', 'disapprover_plan_rel', 'plan_id', 'approver_id', string='Disapprovers', readonly=True)
    approver_message_ids = fields.Many2many('mail.message', 'approver_message_plan_rel', 'plan_id', 'message_id', string='Approver Messages', readonly=True)

    def write(self, values):
        res = super().write(values)
        if 'approver_ids' in values:
            self.calculate_approver_level()
        return res

    def calculate_approver_level(self):
        company = self.company_id or self.partner_id.company_id or self.env.company
        if company.payment_plan_approver_ok:
            level_max = max(company.payment_plan_approver_ids.mapped('level'))
            plans = self.env['payment.plan']
            for plan in self:
                level = plan.approver_level or 0
                for line in company.payment_plan_approver_ids.filtered(lambda l: l.level > level):
                    if all(approver_id in plan.approver_ids.ids for approver_id in line.partner_ids.ids):
                        level = line.level
                if level == level_max:
                    plan.approver_level = -1
                elif level > plan.approver_level:
                    plan.approver_level = level
                    plans |= plan

            if plans:
                partners = company.payment_plan_approver_ids.mapped('partner_ids')
                wizard = self.env['payment.plan.approve'].with_context(active_ids=plans.ids).create({
                    'partner_ids': [(6, 0, partners.ids)],
                    'plan_ids': [(6, 0, plans.ids)],
                    'level': line.level,
                })
                wizard.action_send_email()

    def process_confirm(self, partner, ids):
        approver = self.env['payment.plan']
        disapprover = self.env['payment.plan']
        for plan in self:
            if plan.id in ids:
                approver |= plan
            else:
                disapprover |= plan

        approver.write({'approver_ids': [(4, partner.id)]})
        approver.action_send_email_approved(partner)

        disapprover.write({'disapprover_ids': [(4, partner.id)]})
        disapprover.action_send_email_disapproved(partner)

    def action_send_email_approved(self, partner):
        if self:
            company = self.env.company
            server = company.mail_server_id
            action = self.env.ref('payment_jetcheckout_system.action_plan')
            template = self.env.ref('payment_jetcheckout_system.mail_template_payment_plan_approved')
            link = '%s/web#action=%s&model=payment.plan&view_type=list' % (self.get_base_url(), action.id)
            users = self.mapped('create_uid')
            context = self.env.context.copy()
            for user in users:
                context = self.env.context.copy()
                context.update({
                    'link': link,
                    'server': server,
                    'company': company,
                    'sender': server.email_formatted or company.email_formatted,
                    'receiver': user.partner_id.email_formatted,
                    'lang': user.partner_id.lang,
                    'partner': partner,
                })
                template.with_context(context).send_mail(user.partner_id.id, force_send=True, email_values={
                    'mail_server_id': server.id,
                })

    def action_send_email_disapproved(self, partner):
        if self:
            company = self.env.company
            server = company.mail_server_id
            template = self.env.ref('payment_jetcheckout_system.mail_template_payment_plan_disapproved')
            users = self.mapped('create_uid')
            for user in users:
                context = self.env.context.copy()
                context.update({
                    'server': server,
                    'company': company,
                    'sender': server.email_formatted or company.email_formatted,
                    'receiver': user.partner_id.email_formatted,
                    'lang': user.partner_id.lang,
                    'partner': partner,
                })
                template.with_context(context).send_mail(user.partner_id.id, force_send=True, email_values={
                    'mail_server_id': server.id,
                })

    def payment(self):
        if self.paid:
            return

        partner = self.create_uid
        company = self.company_id or self.partner_id.company_id or self.env.company
        if company.payment_plan_approver_ok:
            level = self.approver_level or 0
            if level >= 0:
                for line in company.payment_plan_approver_ids:
                    if partner.id in line.partner_ids.ids:
                        level = line.level + 1
                        break
                line = fields.first(company.payment_plan_approver_ids.filtered(lambda l: l.level > level))
                if line:
                    wizard = self.env['payment.plan.approve'].create({
                        'partner_ids': [(6, 0, line.partner_ids.ids)],
                        'plan_ids': [(6, 0, self.env.context.get('active_ids', self.ids))],
                        'level': line.level,
                    })
                    action = self.env.ref('payment_jetcheckout_system.action_plan_approve').sudo().read()[0]
                    action['res_id'] = wizard.id
                    return action

        acquirer = self.env['payment.acquirer'].sudo()._get_acquirer(company=company, providers=['jetcheckout'], limit=1, raise_exception=False)
        if not acquirer:
            self.message = _('No acquirer found')
            return

        website = self.env['website'].sudo().search([('company_id', '=', company.id)])
        if not website:
            self.message = _('No website found')
            return

        reference = self.item_id.bank_ref
        if not reference:
            self.message = _('%s must have at least one bank account which is verified.' % self.partner_id.name)
            return

        installment_count = self.installment_id.count or 1
        if installment_count < 1:
            installment_count = 1

        url_query = []
        url_params = self.env.context.get('params', {})
        if 'action' in url_params:
            url_query.append('action=%s' % url_params['action'])
        if 'model' in url_params:
            url_query.append('model=%s' % url_params['model'])
        if 'cids' in url_params:
            url_query.append('cids=%s' % url_params['cids'])
        if 'id' in url_params:
            url_query.append('id=%s' % url_params['id'])
        if 'menu_id' in url_params:
            url_query.append('menu_id=%s' % url_params['menu_id'])
        if 'view_type' in url_params:
            url_query.append('view_type=%s' % url_params['view_type'])
        if 'active_id' in url_params:
            url_query.append('active_id=%s' % url_params['active_id'])
        if url_query:
            url_query = '#' + '&'.join(url_query)
        else:
            url_query = ''

        data = {
            'type': 'virtual_pos',
            'payment': False,
            'threed': company.payment_plan_threed_ok,
            'card': {
                'type': self.token_id.jetcheckout_type or '',
                'program': self.token_id.jetcheckout_program or '',
                'family': self.token_id.jetcheckout_family or '',
                'holder': self.token_id.jetcheckout_holder or '',
                'token': self.token_id.id or 0,
            },
            'amount': self.amount,
            'item': self.item_id,
            'token': self.token_id,
            'partner': self.partner_id,
            'currency': self.currency_id,
            'successurl': '/my/plan/success',
            'failurl': '/my/plan/fail',
            'website': website,
            'installment': {
                'id': installment_count,
                'index': 0,
                'rows': [{
                    'id': installment_count,
                    'count': installment_count,
                    'plus': 0,
                    'irate': 0.0,
                    'crate': 0.0,
                    'corate': 0.0,
                    'idesc': _('%s Installment') % installment_count if installment_count > 1 else _('Single Payment'),
                }],
            },
            'request': {
                'address': request.httprequest.remote_addr,
                'referrer': request.httprequest.referrer + url_query,
            },
            'submerchant': {
                'ref': reference,
                'price': self.amount,
            },
            'campaign': '',
        }

        result = acquirer.action_payment(options=dict(simulate=True), **data)
        if result.get('ok'):
            self.write({'transaction_ids': [(4, result['id'])]})
            self.item_id.write({'transaction_ids': [(4, result['id'])]})
        if result.get('url'):
            if company.payment_plan_fullscreen_ok:
                return {
                    'type': 'ir.actions.act_url',
                    'url': result['url'],
                    'target': 'self',
                }
            else:
                action = self.env.ref('payment_jetcheckout_system.action_plan_pay').sudo().read()[0]
                action['context'] = {'default_data': json.dumps({'url': result['url']})}
                return action
        else:
            self.message = result.get('message') or result.get('error') or _('An error occured')

    def approve(self):
        if self.approval_state == '+':
            return

        transactions = self.transaction_ids.filtered(lambda tx: tx.state == 'done')
        if not transactions:
            self.approval_result = _('Only paid transactions can be approved')
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
            action = plan.payment()
            if action:
                return action

    def action_payment_page(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '%s/p/plan/%s' % (self.get_base_url(), self.uid)
        }

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

    def unlink(self):
        for plan in self:
            if plan.paid:
                raise UserError(_('Paid payment plans cannot be deleted'))
        return super().unlink()


class PaymentPlanPay(models.TransientModel):
    _name = 'payment.plan.pay'
    _description = 'Payment Plan Pay'

    @api.depends('data')
    def _compute_iframe(self):
        for wizard in self:
            data = json.loads(wizard.data)
            if data.get('url'):
                wizard.show = True
                wizard.iframe = '<iframe src="%s" class="position-absolute w-100 h-100 border-0" style="inset:0" onload="paymentPlanIframeLoaded()"></iframe>' % data['url']
            else:
                wizard.show = False
                wizard.iframe = '<div class="alert alert-danger text-center p-3 h5">%s</div>' % _('An error occured. Please try again later.')

    iframe = fields.Html(string='Iframe', compute='_compute_iframe', sanitize=False)
    show = fields.Boolean(string='Show Iframe', compute='_compute_iframe')
    data = fields.Char(readonly=True)


class PaymentPlanWizard(models.TransientModel):
    _name = 'payment.plan.wizard'
    _description = 'Payment Plan Wizard'

    @api.depends('item_ids', 'line_ids.amount_cost', 'line_ids.token_limit_card')
    def _compute_desc(self):
        for wizard in self:
            currency = self.env.company.currency_id
            amount_sum = sum(wizard.item_ids.mapped('amount'))
            amount_planned = sum(wizard.item_ids.mapped('planned_amount'))
            amount_lines = [[line.token_limit_card, line.amount_cost] for line in wizard.line_ids]

            amount_residual = amount_sum - amount_planned
            amount_cost = 0
            amount_total = 0

            for line in amount_lines:
                if line[0] > amount_residual:
                    residual_cost = amount_residual * line[1] / line[0] if line[0] else 0.0
                    amount_total += amount_residual + residual_cost
                    amount_cost += residual_cost
                    amount_residual = 0
                    break
                else:
                    amount_total += line[0] + line[1]
                    amount_cost += line[1]
                    amount_residual -= line[0]

            amount_total = float_round(amount_total, precision_rounding=currency.rounding)
            amount_cost = float_round(amount_cost, precision_rounding=currency.rounding)
            desc_amount = formatLang(self.env, amount_total, currency_obj=currency)
            desc_count = len(wizard.item_ids)
            desc = _('<strong class="text-primary">%s</strong> partner(s) selected. Total amount is <strong class="text-primary">%s</strong>.' % (desc_count, desc_amount))
            if amount_cost:
                desc_cost = formatLang(self.env, amount_cost, currency_obj=currency)
                desc += ' ' + _('Total cost is <strong class="text-primary">%s</strong>.' % (desc_cost,))
            if amount_residual:
                desc_residual = formatLang(self.env, amount_residual, currency_obj=currency)
                desc += ' ' + _('Residual amount is <strong class="text-600">%s</strong>.' % (desc_residual,))
            wizard.desc = desc

    @api.depends('line_ids.token_id')
    def _compute_token_ids(self):
        for wizard in self:
            wizard.token_ids = [(6, 0, wizard.line_ids.mapped('token_id').ids)]

    item_ids = fields.Many2many('payment.item', 'item_plan_wizard_rel', 'wizard_id', 'item_id', string='Items', readonly=True)
    desc = fields.Html(sanitize=False, compute='_compute_desc')
    line_ids = fields.One2many('payment.plan.wizard.line', 'wizard_id', string='Lines')
    token_ids = fields.Many2many('payment.token', compute='_compute_token_ids')

    def action_confirm(self):
        values = []
        lines = [[line.token_id.id, line.installment_id.id, line.token_limit_card, line.token_limit_tx] for line in self.line_ids]
        for item in self.item_ids:
            amount = item.amount - item.planned_amount
            for line in lines:
                while line[2] > 0 and amount > 0:
                    if line[3] > amount:
                        line_amount = amount
                    elif line[2] > line[3]:
                        line_amount = line[3]
                    else:
                        line_amount = line[2]
                    values.append({
                        'date': item.date,
                        'item_id': item.id,
                        'partner_id': item.parent_id.id,
                        'amount': line_amount,
                        'token_id': line[0],
                        'installment_id': line[1],
                    })
                    line[2] -= line_amount
                    amount -= line_amount
                if not amount > 0:
                    break

        plans = self.env['payment.plan'].create(values)
        action = self.env.ref('payment_jetcheckout_system.action_plan').sudo().read()[0]
        action['domain'] = [('id', 'in', plans.ids)]
        return action


class PaymentPlanWizardLine(models.TransientModel):
    _name = 'payment.plan.wizard.line'
    _description = 'Payment Plan Wizard Line'

    @api.depends('token_id')
    def _compute_installment(self):
        for line in self:
            data = {}
            message = ''
            token = line.token_id
            installments = { 1 }
            installments_search = self.env['payment.acquirer.jetcheckout.installment'].search
            if token:
                acquirer = token.acquirer_id
                currency = token.company_id.currency_id
                campaign = acquirer.jetcheckout_campaign_id.name or ''
                url = '%s/api/v1/prepayment/bin_installment_options' % (acquirer._get_paylox_api_url(),)

                response = requests.post(url, data=json.dumps({
                    "application_key": acquirer.jetcheckout_api_key,
                    "mode": acquirer._get_paylox_env(),
                    "card_token": token.acquirer_ref,
                    "currency": currency.name,
                    "campaign_name": campaign,
                    "language": "tr",
                    #"amount": int(float_round(amount, 2) * 100),
                }))
                if response.status_code == 200:
                    result = response.json()
                    if result['response_code'] == "00":
                        options = result.get('installments')
                        if not options:
                            message = _('No installment found (Error Code: -1)')
                        else:
                            for option in options:
                                lines = option.get('installments', [])
                                for i in lines:
                                    count = i.get('installment_count', 1)
                                    data.update({ count: i })
                                    installments.add(count)
                    else:
                        message = _('%s (Error Code: %s)') % (result['message'], result['response_code'])
                else:
                    message = _('%s (Error Code: %s)') % (response.reason, response.status_code)

            installments_filtered = installments_search([('count', 'in', list(installments))]).ids
            line.installment_message = message and f'<i class="fa fa-info-circle text-danger" title="{ message }"/>'
            line.installment_ids = [(6, 0, installments_filtered)]
            line.installment_data = json.dumps(data)

    @api.depends('installment_id', 'token_limit_card')
    def _compute_amount_cost(self):
        for line in self:
            data = json.loads(line.installment_data)
            installment = data.get(str(line.installment_id.count), {})
            line.amount_cost = installment.get('customer_rate', 0) * line.token_limit_card / 100

    wizard_id = fields.Many2one('payment.plan.wizard')
    token_id = fields.Many2one('payment.token', string='Credit Card', domain='[("id", "not in", parent.token_ids), ("verified", "=", True)]', required=True)
    token_limit_card = fields.Float(string='Card Limit')
    token_limit_tx = fields.Float(string='Transaction Limit')
    installment_id = fields.Many2one('payment.acquirer.jetcheckout.installment', string='Installment', domain='[("id", "in", installment_ids)]', default=lambda self: self.env.ref('payment_jetcheckout.installment_1'))
    installment_message = fields.Html(string='Installment Message', sanitize=False, compute='_compute_installment', compute_sudo=True)
    installment_ids = fields.Many2many('payment.acquirer.jetcheckout.installment', string='Installments', compute='_compute_installment', compute_sudo=True)
    installment_data = fields.Text(string='Installment Data', compute='_compute_installment', compute_sudo=True, store=True)
    amount_cost = fields.Monetary(string='Cost Amount', compute='_compute_amount_cost', store=True)
    currency_id = fields.Many2one(related='token_id.company_id.currency_id')

    @api.constrains('token_limit_tx')
    def check_token_limit_tx(self):
        for line in self:
            if not line.token_limit_tx > 0:
                raise UserError(_('Transaction limit must be higher than zero!'))

    @api.onchange('token_id')
    def onchange_token_id(self):
        self.installment_id = self.env.ref('payment_jetcheckout.installment_1').id
        self.token_limit_card = self.token_id.jetcheckout_limit_card if self.token_id else 0
        self.token_limit_tx = self.token_id.jetcheckout_limit_tx if self.token_id else 0


class PaymentPlanErrorWizard(models.TransientModel):
    _name = 'payment.plan.error.wizard'
    _description = 'Payment Plan Error Wizard'

    item_ids = fields.Many2many('payment.item', 'item_plan_error_wizard_rel', 'wizard_id', 'item_id', string='Items', readonly=True)


class PaymentPlanApprover(models.Model):
    _name = 'payment.plan.approver'
    _description = 'Payment Plan Approvers'
    _order= 'level,sequence,id'

    sequence = fields.Integer(default=10)
    company_id = fields.Many2one('res.company')
    partner_ids = fields.Many2many('res.partner', 'payment_plan_approver_partner_rel', 'approver_id', 'partner_id', string='Partners')
    level = fields.Integer(default=1)

    @api.constrains('level')
    def _check_level(self):
        for approver in self:
            if not approver.level or approver.level < 1:
                raise UserError(_('Approver level must be higher than zero'))


class PaymentPlanApprove(models.TransientModel):
    _name = 'payment.plan.approve'
    _description = 'Payment Plan Approve'

    partner_ids = fields.Many2many('res.partner', 'payment_plan_approve_partner_rel', 'approver_id', 'partner_id', string='Partners')
    plan_ids = fields.Many2many('payment.plan', 'payment_plan_approve_plan_rel', 'approver_id', 'plan_id', string='Plans')
    level = fields.Integer(default=0)

    def action_send_email(self):
        company = self.env.company
        server = company.mail_server_id
        template = self.env.ref('payment_jetcheckout_system.mail_template_payment_plan_approve')
        line = fields.first(company.payment_plan_approver_ids.filtered(lambda l: l.level > self.level))
        partners = line.mapped('partner_ids').filtered(lambda p: p.payment_plan_approver_state not in ('approved', 'disapproved'))
        plans = {}
        for plan in self.plan_ids:
            if plan.create_uid.id not in plans:
                plans[plan.create_uid.id] = self.env['payment.plan']
            plans[plan.create_uid.id] |= plan
        for partner in partners:
            for uid, plan in plans.items():
                user = self.env['res.users'].browse(uid)
                plan_uids = ','.join(plan.mapped('uid'))
                link = '%s/p/plan/%s/approve/%s' % (self.get_base_url(), plan_uids, partner._get_token())
                context = self.env.context.copy()
                context.update({
                    'link': link,
                    'server': server,
                    'company': company,
                    'domain': urlparse(link).netloc,
                    'sender': server.email_formatted or company.email_formatted,
                    'receiver': partner.email_formatted,
                    'lang': partner.lang,
                    'user': user,
                })
                template.with_context(context).send_mail(partner.id, force_send=True, email_values={
                    'mail_server_id': server.id,
                })
