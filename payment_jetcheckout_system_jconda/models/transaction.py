# -*- coding: utf-8 -*-
from odoo import fields, models

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    jetcheckout_connector_state = fields.Boolean('Connector State', readonly=True)
    jetcheckout_connector_partner_name = fields.Char('Connector Partner Name', readonly=True)
    jetcheckout_connector_partner_vat = fields.Char('Connector Partner VAT', readonly=True)

    def action_process_connector(self):
        self.ensure_one()
        if not self.jetcheckout_connector_state:
            return

        line = self.acquirer_id._get_journal_line(name=self.jetcheckout_vpos_name, user=self.env.user)
        result = self.env['jconda.connector'].sudo()._execute('payment_post_partner_payment', params={
            'account_name': line and line.journal_id.default_account_id.code or '',
            'transaction_id': self.jetcheckout_transaction_id,
            'pos_name': self.jetcheckout_vpos_name,
            'date': self.last_state_change.strftime('%Y-%m-%d'),
            'vat': self.jetcheckout_connector_partner_vat or self.partner_id.vat,
            'card_number': self.jetcheckout_card_number,
            'installments': self.jetcheckout_installment_description,
            'currency_name': self.currency_id.name,
            'amount': self.jetcheckout_payment_amount,
            'amount_commission_cost': self.jetcheckout_commission_amount,
            'amount_customer_cost': self.jetcheckout_customer_amount
        }, company=self.company_id)
        self.jetcheckout_connector_state = result == None

    def _jetcheckout_done_postprocess(self):
        super()._jetcheckout_done_postprocess()
        self.write({'jetcheckout_connector_state': True})
        self.action_process_connector()
