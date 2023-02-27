# -*- coding: utf-8 -*-
from odoo import fields, models, _

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    jetcheckout_connector_ok = fields.Boolean('Connector Transaction', readonly=True)
    jetcheckout_connector_state = fields.Boolean('Connector State', readonly=True)
    jetcheckout_connector_partner_name = fields.Char('Connector Partner Name', readonly=True)
    jetcheckout_connector_partner_vat = fields.Char('Connector Partner VAT', readonly=True)
    jetcheckout_connector_state_message = fields.Text('Connector State Message', readonly=True)

    def action_process_connector(self):
        self.ensure_one()
        if not self.jetcheckout_connector_ok or not self.jetcheckout_connector_state:
            return

        line = self.acquirer_id._get_branch_line(name=self.jetcheckout_vpos_name, user=self.create_uid)
        vat = self.jetcheckout_connector_partner_vat or self.partner_id.vat
        result = self.env['syncops.connector'].sudo()._execute('payment_post_partner_payment', params={
            'account_code': vat,
            'transaction_id': self.jetcheckout_transaction_id,
            'pos_name': line and line.account_code or '',
            'date': self.last_state_change.strftime('%Y-%m-%d %H:%M:%S'),
            'vat': vat,
            'card_number': self.jetcheckout_card_number,
            'card_name': self.jetcheckout_card_name,
            'installments': self.jetcheckout_installment_description,
            'currency_name': self.currency_id.name,
            'amount': self.amount,
            'amount_commission_cost': self.jetcheckout_commission_amount,
            'amount_customer_cost': self.jetcheckout_customer_amount,
            'amount_commission_rate': self.jetcheckout_commission_rate,
            'amount_customer_rate': self.jetcheckout_customer_rate,
            'description': self.state_message
        }, company=self.company_id, message=True)

        state = result[0] == None
        if state:
            self.write({
                'jetcheckout_connector_state': True,
                'jetcheckout_connector_state_message': _('This transaction has not been successfully posted to connector.\n%s') % result[1]
            })
        else:
            self.write({
                'jetcheckout_connector_state': False,
                'jetcheckout_connector_state_message': _('This transaction has been successfully posted to connector.')
            })

    def _jetcheckout_done_postprocess(self):
        super()._jetcheckout_done_postprocess()
        if self.jetcheckout_connector_ok:
            self.write({
                'jetcheckout_connector_state': True,
                'jetcheckout_connector_state_message': _('This transaction has not been posted to connector yet.')
            })
            self.action_process_connector()
