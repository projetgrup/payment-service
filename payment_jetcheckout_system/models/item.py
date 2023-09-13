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

    @api.depends('amount', 'paid_amount')
    def _compute_residual(self):
        for item in self:
            item.residual_amount = item.amount - item.paid_amount

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
    amount = fields.Monetary()
    date = fields.Date()
    due_date = fields.Date()
    due_amount = fields.Float(compute='_compute_due_amount')
    file = fields.Binary()
    paid = fields.Boolean()
    ref = fields.Char()
    description = fields.Char()
    is_admin = fields.Boolean(compute='_compute_is_admin')
    paid_amount = fields.Monetary(readonly=True)
    residual_amount = fields.Monetary(compute='_compute_residual', store=True, readonly=True)
    installment_count = fields.Integer(readonly=True)
    paid_date = fields.Datetime(readonly=True)
    vat = fields.Char(related='parent_id.vat', string='VAT', store=True)
    campaign_id = fields.Many2one(related='parent_id.campaign_id', string='Campaign')
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
        if 'paid' in values and not values['paid']:
            values['paid_amount'] = 0
        res = super().write(values)
        for item in self:
            if not item.system:
                item.system = item.company_id.system or item.parent_id.system or item.child_id.system
            if not item.currency_id:
                item.currency_id = item.company_id.currency_id.id
        return res

    def get_due(self):
        self = self.filtered(lambda x: not x.paid)

        today = fields.Date.today()
        total = sum(self.mapped('residual_amount'))
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
            for item in self:
                if base == 'date_document':
                    date = item.date
                    sign = -1
                else:
                    date = item.due_date
                    sign = 1
                if not date:
                    date = today
                diff = date - today
                amount += item.residual_amount * diff.days * sign

            days = amount/total if total else 0
            date = (today + timedelta(days=days)).strftime(lang.date_format)
            days, campaign = company.payment_page_due_ids.get_campaign(days)
            if days == False:
                hide_payment = True
                hide_payment_message = company.payment_page_due_hide_payment_message

        return {
            'amount': amount,
            'days': days,
            'date': date,
            'campaign': campaign,
            'hide_payment': hide_payment,
            'hide_payment_message': hide_payment_message,
        }
