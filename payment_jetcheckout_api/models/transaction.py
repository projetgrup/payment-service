# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    jetcheckout_api_ok = fields.Boolean('API Active', readonly=True, copy=False)
    jetcheckout_api_contact = fields.Char('API Contact', readonly=True)
    jetcheckout_api_order = fields.Char('API Order', readonly=True)
    jetcheckout_api_product = fields.Char('API Product', readonly=True)
    jetcheckout_api_hash = fields.Char('API Hash', readonly=True)
    jetcheckout_api_id = fields.Char('API TransactionID', readonly=True)
    jetcheckout_api_html = fields.Html('API HTML', sanitize=False, readonly=True)
    jetcheckout_api_success_url = fields.Char('API Success URL', readonly=True)
    jetcheckout_api_fail_url = fields.Char('API Fail URL', readonly=True)

    jetcheckout_api_card_return_url = fields.Char('API Card Return URL', readonly=True)
    jetcheckout_api_card_result_url = fields.Char('API Card Result URL', readonly=True)
    jetcheckout_api_card_redirect_url = fields.Char('API Card Redirect URL', readonly=True)
    jetcheckout_api_bank_redirect_url = fields.Char('API Bank Return URL', readonly=True)
    jetcheckout_api_bank_webhook_url = fields.Char('API Bank Webhook URL', readonly=True)
    jetcheckout_api_credit_redirect_url = fields.Char('API Credit Return URL', readonly=True)
    jetcheckout_api_credit_result_url = fields.Char('API Credit Result URL', readonly=True)

    paylox_api_method_ids = fields.One2many('payment.transaction.paylox.api.method', 'transaction_id', string='API Methods', readonly=True)

    def write(self, values):
        if 'jetcheckout_payment_ok' in values and any(tx.jetcheckout_api_ok for tx in self):
            values['jetcheckout_payment_ok'] = False
        return super().write(values)

    def _paylox_done_postprocess(self):
        res = super()._paylox_done_postprocess()
        if self.jetcheckout_payment_type == 'physicalpos':
            method = fields.first(self.paylox_api_method_ids.filtered(lambda m: m.type == 'physicalpos'))
            if method.webhook_url:
                try:
                    requests.post(method.webhook_url, data=json.dumps({
                        'success': True,
                        'id': self.jetcheckout_api_id or None,
                        'ref': self.jetcheckout_transaction_id or None,
                        'amount': self.amount or None,
                    }), timeout=15)
                except:
                    _logger.error('An error occured when triggering physical PoS webhook.', exc_info=True)
        return res


class PaymentTransactionPayloxApiMethod(models.Model):
    _name = 'payment.transaction.paylox.api.method'
    _description = 'Payment Transaction Paylox API Methods'

    @api.depends('type')
    def _compute_code(self):
        for method in self:
            if method.type == 'virtualpos':
                method.code = 'card'
            elif method.type == 'physicalpos':
                method.code = 'pos'
            elif method.type == 'softpos':
                method.code = 'mobile'
            else:
                method.code = method.type

    @api.depends('type')
    def _compute_icon(self):
        for method in self:
            if method.type == 'virtualpos':
                method.icon = 'credit-card'
            elif method.type == 'physicalpos':
                method.icon = 'fax'
            elif method.type == 'softpos':
                method.icon = 'mobile-phone'
            elif method.type == 'transfer':
                method.icon = 'bank'
            elif method.type == 'wallet':
                method.icon = 'money'
            elif method.type == 'credit':
                method.icon = 'shopping-cart'
            else:
                method.icon = False

    transaction_id = fields.Many2one('payment.transaction')
    type = fields.Selection(selection=[
        ('virtualpos', 'Virtual PoS'),
        ('physicalpos', 'Physical PoS'),
        ('softpos', 'Soft PoS'),
        ('transfer', 'Bank Transfer'),
        ('wallet', 'Wallet'),
        ('credit', 'Shopping Credit'),
    ], default='virtualpos')
    code = fields.Char(compute='_compute_code')
    icon = fields.Char(compute='_compute_icon')
    redirect_url = fields.Char(string='Redirect URL')
    webhook_url = fields.Char(string='Webhook URL')
    type_physicalpos_ids = fields.Many2many('payment.method.physicalpos', 'payment_transaction_api_method_physicalpos_rel', 'method_id', 'pos_id', string='Physical PoS IDs')
