# -*- coding: utf-8 -*-
from odoo import fields, models, api


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

    transaction_id = fields.Many2one('payment.transaction')
    type = fields.Selection(selection=[
        ('virtualpos', 'Virtual PoS'),
        ('physicalpos', 'Physical PoS'),
        ('softpos', 'Soft PoS'),
        ('transfer', 'Bank Transfer'),
        ('wallet', 'Wallet'),
        ('credit', 'Shopping Credit'),
    ], default='virtualpos')
    code = fields.Char(compute='_compute_code', store=True)
    redirect_url = fields.Char(string='Redirect URL')
    webhook_url = fields.Char(string='Webhook URL')
