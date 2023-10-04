# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api
from odoo.tools.misc import get_lang


class PaymentItem(models.Model):
    _name = 'payment.item'
    _description = 'Payment Items'
    _order = 'id desc'

    def _compute_name(self):
        for payment in self:
            payment.name = payment.parent_id.name

    def _compute_is_admin(self):
        is_admin = self.env.user.has_group('base.group_system')
        for payment in self:
            payment.is_admin = is_admin

    @api.onchange('child_id')
    def _onchange_child_id(self):
        self.parent_id = self.child_id.parent_id.id if self.child_id else False

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        self.child_id = self.parent_id.child_ids and self.parent_id.child_ids[0].id if self.parent_id else False

    @api.depends('residual_amount')
    def _compute_paid(self):
        for item in self:
            if item.residual_amount:
                item.paid = False
                item.paid_date = False
                item.installment_count = False
            else:
                item.paid = True
                transactions = item.transaction_ids.filtered(lambda x: x.state == 'done')
                if transactions:
                    transaction = transactions[0]
                    item.paid_date = transaction.last_state_change
                    item.installment_count = transaction.jetcheckout_installment_count
                else:
                    item.paid_date = False
                    item.installment_count = False

    @api.depends('transaction_ids.state')
    def _compute_paid_amount(self):
        for item in self:
            items = self.env['payment.transaction.item'].sudo().search([
                ('item_id', '=', item.id),
                ('transaction_id.state', '=', 'done'),
            ])
            amount = item.amount
            paid = sum(items.mapped('amount'))
            item.paid_amount = amount if paid > amount else paid

    @api.depends('amount', 'paid_amount')
    def _compute_residual_amount(self):
        for item in self:
            residual = item.amount - item.paid_amount
            item.residual_amount = residual if residual > 0 else 0

    @api.depends('amount', 'date', 'due_date')
    def _compute_due_amount(self):
        today = fields.Date.today()
        base = self.env.company.payment_page_due_base
        for item in self:
            date = item.date if base == 'date_document' else item.due_date
            diff = date - today
            item.due_amount = item.amount * diff.days

    name = fields.Char(compute='_compute_name')
    child_id = fields.Many2one('res.partner', ondelete='restrict')
    parent_id = fields.Many2one('res.partner', ondelete='restrict')
    vat = fields.Char(related='parent_id.vat', string='VAT', store=True)
    campaign_id = fields.Many2one(related='parent_id.campaign_id', string='Campaign')

    amount = fields.Monetary()
    date = fields.Date()
    due_date = fields.Date()
    due_amount = fields.Float(compute='_compute_due_amount')

    file = fields.Binary()
    ref = fields.Char()
    description = fields.Char()

    paid = fields.Boolean(compute='_compute_paid', store=True, readonly=True)
    paid_amount = fields.Monetary(compute='_compute_paid_amount', store=True, readonly=True)
    residual_amount = fields.Monetary(compute='_compute_residual_amount', store=True, readonly=True)
    installment_count = fields.Integer(compute='_compute_paid', store=True, readonly=True)
    paid_date = fields.Datetime(compute='_compute_paid', store=True, readonly=True)
    is_admin = fields.Boolean(compute='_compute_is_admin')

    transaction_ids = fields.Many2many('payment.transaction', 'transaction_item_rel', 'item_id', 'transaction_id', string='Transactions')
    system = fields.Selection(selection=[], readonly=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company, readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)

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

    @api.model
    def create(self, values):
        res = super().create(values)
        if not res.system:
            res.system = res.company_id.system or res.parent_id.system or res.child_id.system
        if not res.currency_id:
            res.currency_id = res.company_id.currency_id.id
        return res

    def write(self, values):
        res = super().write(values)
        for item in self:
            if not item.system:
                item.system = item.company_id.system or item.parent_id.system or item.child_id.system
            if not item.currency_id:
                item.currency_id = item.company_id.currency_id.id
        return res

    def get_due(self):
        self = self.filtered(lambda x: not x.paid)

        amounts = self.env.context.get('amounts', {})
        total = 0
        for item in self:
            total += amounts.get(item.id, item.residual_amount)

        today = fields.Date.today()
        amount = 0
        days = 0
        date = False
        campaign = ''
        hide_payment = False
        hide_payment_message = ''

        company = self.env.company
        lang = get_lang(self.env)
        if company.payment_page_due_ok:
            base = company.payment_page_due_base
            sign = -1 if base == 'date_document' else 1
            for item in self:
                date = item.due_date if sign == 1 else item.date
                if not date:
                    date = today
                diff = date - today
                residual = amounts.get(item.id, item.residual_amount)
                amount += residual * diff.days

            days = amount/total if total else 0
            date = (today + timedelta(days=days)).strftime(lang.date_format)
            days, campaign, hide_payment = company.payment_page_due_ids.get_campaign(days * sign)
            if hide_payment:
                hide_payment_message = company.payment_page_due_hide_payment_message

        return {
            'amount': amount,
            'days': days,
            'date': date,
            'campaign': campaign,
            'hide_payment': hide_payment,
            'hide_payment_message': hide_payment_message,
        }
