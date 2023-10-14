# -*- coding: utf-8 -*-
from odoo import fields, models, _

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    jetcheckout_connector_ok = fields.Boolean('Connector Transaction', readonly=True)
    jetcheckout_connector_ref = fields.Char('Connector Reference', readonly=True)
    jetcheckout_connector_state = fields.Boolean('Connector State', readonly=True)
    jetcheckout_connector_partner_name = fields.Char('Connector Partner Name', readonly=True)
    jetcheckout_connector_partner_vat = fields.Char('Connector Partner VAT', readonly=True)
    jetcheckout_connector_partner_ref = fields.Char('Connector Partner Reference', readonly=True)
    jetcheckout_connector_state_message = fields.Text('Connector State Message', readonly=True)

    def action_syncops_xlsx(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/syncops/payment/transactions/xlsx?=%s' % ','.join(map(str, self.ids))
        }

    def action_process_connector(self):
        self.ensure_one()
        #if not self.jetcheckout_connector_ok or not self.jetcheckout_connector_state:
        #    return

        vat = self.jetcheckout_connector_partner_vat or self.partner_id.vat
        ref = self.jetcheckout_connector_partner_ref or self.partner_id.ref
        name = self.jetcheckout_connector_partner_name or self.partner_id.name
        line = self.acquirer_id._get_branch_line(name=self.jetcheckout_vpos_name, user=self.create_uid)
        result = self.env['syncops.connector'].sudo()._execute('payment_post_partner_payment', params={
            'id': self.id,
            'ref': ref,
            'vat': vat,
            'name': name,
            'amount': self.amount,
            'reference': self.reference,
            'provider': self.acquirer_id.provider,
            'currency_name': self.currency_id.name,
            'company_id': self.company_id.partner_id.ref,
            'account_code': line.account_code if line else '',
            'state': 'refund' if self.source_transaction_id else self.state,
            'date': self.last_state_change.strftime('%Y-%m-%d %H:%M:%S'),
            'card_number': self.jetcheckout_card_number or '',
            'card_name': self.jetcheckout_card_name,
            'order_id': self.source_transaction_id.jetcheckout_order_id if self.source_transaction_id else self.jetcheckout_order_id,
            'transaction_id': self.source_transaction_id.jetcheckout_transaction_id if self.source_transaction_id else self.jetcheckout_transaction_id,
            'virtual_pos_id': self.jetcheckout_vpos_id or 0,
            'installment_count': self.jetcheckout_installment_count or 1,
            'installment_plus': self.jetcheckout_installment_plus or 0,
            'installment_code': self.jetcheckout_campaign_name or '',
            'installments': self.jetcheckout_installment_description or '',
            'amount_commission_cost': self.jetcheckout_commission_amount or 0,
            'amount_customer_cost': self.jetcheckout_customer_amount or 0,
            'amount_commission_rate': self.jetcheckout_commission_rate or 0,
            'amount_customer_rate': self.jetcheckout_customer_rate or 0,
            'description': self.state_message,
        }, company=self.company_id, message=True)

        if result[0] == None:
            self.write({
                'jetcheckout_connector_ref': False,
                'jetcheckout_connector_state': True,
                'jetcheckout_connector_state_message': _('This transaction has not been successfully posted to connector.\n%s') % result[1]
            })
        else:
            self.write({
                'jetcheckout_connector_ref': result[0] and result[0][0].get('ref', False) or False,
                'jetcheckout_connector_state': False,
                'jetcheckout_connector_state_message': _('This transaction has been successfully posted to connector.')
            })

    def _paylox_done_postprocess(self):
        res = super()._paylox_done_postprocess()
        if self.jetcheckout_connector_ok:
            self.write({
                'jetcheckout_connector_state': True,
                'jetcheckout_connector_state_message': _('Successful status of this transaction has not been posted to connector yet.')
            })
            self.action_process_connector()
        return res

    def _paylox_cancel_postprocess(self):
        res = super()._paylox_cancel_postprocess()
        if self.jetcheckout_connector_ok:
            self.write({
                'jetcheckout_connector_state': True,
                'jetcheckout_connector_state_message': _('Cancelled status of this transaction has not been posted to connector yet.')
            })
            self.action_process_connector()
        return res

    def _paylox_refund_postprocess(self, amount=0):
        res = super()._paylox_refund_postprocess(amount=amount)
        if self.jetcheckout_connector_ok:
            res.write({
                'jetcheckout_connector_ok': True,
                'jetcheckout_connector_state': True,
                'jetcheckout_connector_state_message': _('Refunded status of this transaction has not been posted to connector yet.')
            })
            res.action_process_connector()
        return res
