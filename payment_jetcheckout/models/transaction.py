# -*- coding: utf-8 -*-
import requests
import logging
import json

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _calc_is_jetcheckout(self):
        for rec in self:
            rec.is_jetcheckout = rec.acquirer_id.provider == 'jetcheckout'

    def _calc_installment_description_long(self):
        for rec in self:
            desc = rec.jetcheckout_installment_description
            desc_long = ''
            try:
                installment = int(desc)
                if installment == 0:
                    desc_long = ''
                elif installment == 1:
                    desc_long = _('Single payment')
                else:
                    desc_long = _('%s installment') % desc
            except:
                desc_long = desc
            rec.jetcheckout_installment_description_long = desc_long

    @api.model
    def _get_default_partner_country_id(self):
        country = self.env.company.country_id
        if not country:
            raise ValidationError(_('Please define a country for this company'))
        return country.id

    partner_vat = fields.Char(string="VAT")
    is_jetcheckout = fields.Boolean(compute='_calc_is_jetcheckout')
    jetcheckout_api_ok = fields.Boolean('API Active', readonly=True, copy=False)
    jetcheckout_card_name = fields.Char('Card Holder Name', readonly=True, copy=False)
    jetcheckout_card_number = fields.Char('Card Number', readonly=True, copy=False)
    jetcheckout_card_type = fields.Char('Card Type', readonly=True, copy=False)
    jetcheckout_card_family = fields.Char('Card Family', readonly=True, copy=False)
    jetcheckout_vpos_name = fields.Char('Virtual Pos', readonly=True, copy=False)
    jetcheckout_order_id = fields.Char('Order', readonly=True, copy=False)
    jetcheckout_ip_address = fields.Char('IP Address', readonly=True, copy=False)
    jetcheckout_transaction_id = fields.Char('Transaction', readonly=True, copy=False)
    jetcheckout_payment_amount = fields.Monetary('Payment Amount', readonly=True, copy=False)
    jetcheckout_installment_count = fields.Integer('Installment Count', readonly=True, copy=False)
    jetcheckout_installment_description = fields.Char('Installment Description', readonly=True, copy=False)
    jetcheckout_installment_description_long = fields.Char('Installment Long Description', readonly=True, compute='_calc_installment_description_long')
    jetcheckout_installment_amount = fields.Monetary('Installment Amount', readonly=True, copy=False)
    jetcheckout_commission_rate = fields.Float('Commission Rate', readonly=True, copy=False)
    jetcheckout_commission_amount = fields.Monetary('Commission Amount', readonly=True, copy=False)
    jetcheckout_customer_rate = fields.Float('Customer Commission Rate', readonly=True, copy=False)
    jetcheckout_customer_amount = fields.Monetary('Customer Commission Amount', readonly=True, copy=False)
    jetcheckout_website_id = fields.Many2one('website', 'Website', readonly=True, copy=False)
    jetcheckout_date_expiration = fields.Datetime('Expiration Date', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if 'partner_vat' not in values:
                partner = self.env['res.partner'].browse(values['partner_id'])
                values.update({'partner_vat': partner.vat})

        txs = super().create(values_list)

        for tx in txs:
            partner_phone = tx.partner_id.mobile or tx.partner_id.phone
            if partner_phone:
                tx.write({'partner_phone': partner_phone})
        return txs

    def _jetcheckout_api_status(self):
        url = '%s/api/v1/payment/status' % self.acquirer_id._get_jetcheckout_api_url()
        data = {
            "application_key": self.acquirer_id.jetcheckout_api_key,
            "order_id": self.jetcheckout_order_id,
            "lang": "tr",
        }

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if result['response_code'] == "00200":
                values = {'result': result}
            else:
                values = {'error': _('%s (Error Code: %s)') % (result['message'], result['response_code'])}
        else:
            values = {'error': _('%s (Error Code: %s)') % (response.reason, response.status_code)}
        return values

    def _jetcheckout_payment_create(self):
        if self.payment_id:
            return

        self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
        payment_method_line = self.env.ref('payment_jetcheckout.payment_method_jetcheckout')
        line = self.acquirer_id.sudo()._get_journal_line(name=self.jetcheckout_vpos_name)
        if not line:
            raise UserError(_('There is no journal line for %s in %s') % (self.jetcheckout_vpos_name, self.acquirer_id.name))

        values = {
            'amount': abs(self.amount),
            'payment_type': 'inbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            'journal_id': line.journal_id.id,
            'company_id': self.acquirer_id.company_id.id,
            'payment_method_line_id': payment_method_line.id,
            'payment_token_id': self.token_id.id,
            'payment_transaction_id': self.id,
            'ref': self.reference,
        }
        payment = self.env['account.payment'].with_context(line=line, skip_account_move_synchronization=True).create(values)
        payment.post_with_jetcheckout(line, self.jetcheckout_commission_amount, self.jetcheckout_ip_address)
        self.payment_id = payment

        if self.invoice_ids:
            self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
            (payment.line_ids + self.invoice_ids.line_ids).filtered(lambda line: line.account_id == payment.destination_account_id and not line.reconciled).reconcile()

    def _jetcheckout_refund_postprocess(self, amount=None):
        values = {
            'jetcheckout_card_name': self.jetcheckout_card_name,
            'jetcheckout_card_number': self.jetcheckout_card_number,
            'jetcheckout_card_type': self.jetcheckout_card_type,
            'jetcheckout_card_family': self.jetcheckout_card_family,
            'jetcheckout_vpos_name': self.jetcheckout_vpos_name,
            'is_post_processed': True,
            'state': 'done',
            'state_message': _('Transaction has been refunded successfully.')
        }
        transaction = self._create_refund_transaction(amount_to_refund=amount, **values)
        transaction._log_sent_message()

    def _jetcheckout_api_refund(self, amount=0.0, **kwargs):
        self.ensure_one()
        url = '%s/api/v1/payment/refund' % self.acquirer_id._get_jetcheckout_api_url()
        data = {
            "application_key": self.acquirer_id.jetcheckout_api_key,
            "order_id": self.jetcheckout_order_id,
            "transaction_id": self.jetcheckout_transaction_id,
            "amount": int(amount * 100),
            "currency": self.currency_id.name,
            "language": "tr",
        }

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if result['response_code'] == "00":
                values = {'result': result}
            else:
                values = {'error': _('%s (Error Code: %s)') % (result['message'], result['response_code'])}
        else:
            values = {'error': _('%s (Error Code: %s)') % (response.reason, response.status_code)}

        if 'error' in values:
            raise UserError(values['error'])
        self._jetcheckout_refund_postprocess(amount)

    def _jetcheckout_api_cancel(self, **kwargs):
        self.ensure_one()
        url = '%s/api/v1/payment/cancel' % self.acquirer_id._get_jetcheckout_api_url()
        data = {
            "application_key": self.acquirer_id.jetcheckout_api_key,
            "order_id": self.jetcheckout_order_id,
            "transaction_id": self.jetcheckout_transaction_id,
            "language": "tr",
        }

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if result['response_code'] in ("00", "01"):
                values = {'result': result}
            else:
                values = {'error': _('%s (Error Code: %s)') % (result['message'], result['response_code'])}
        else:
            values = {'error': _('%s (Error Code: %s)') % (response.reason, response.status_code)}
        return values

    def _jetcheckout_done_postprocess(self):
        if not self.state == 'done':
            self.write({'state': 'done'})
            self.jetcheckout_order_confirm()
            self.jetcheckout_payment()
            self.is_post_processed = True

    def jetcheckout_order_confirm(self):
        self.ensure_one()
        orders = hasattr(self, 'sale_order_ids') and self.sale_order_ids
        if not orders:
            return
        try:
            self.env.cr.commit()
            orders.filtered(lambda x: x.state not in ('sale','done')).with_context(send_email=True).action_confirm()
        except Exception as e:
            self.env.cr.rollback()
            _logger.error('Confirming order for transaction %s is failed\n%s' % (self.reference, e))

    def jetcheckout_payment(self):
        self.ensure_one()
        try:
            self.env.cr.commit()
            self.sudo()._jetcheckout_payment_create()
            self.write({
                'state_message': _('Transaction is succesful and payment has been validated.'),
            })
        except Exception as e:
            self.env.cr.rollback()
            self.write({
                'state_message': _('Transaction is succesful, but payment could not be validated. Probably one of partner or journal accounts are missing.') + '\n' + str(e),
            })
            _logger.warning('Creating payment for transaction %s is failed\n%s' % (self.reference, e))

    def _jetcheckout_cancel_postprocess(self):
        if not self.state == 'cancel':
            self.write({
                'state': 'cancel',
                'state_message': _('Transaction has been cancelled successfully.')
            })

    def _jetcheckout_cancel(self):
        self.ensure_one()
        values = self._jetcheckout_api_cancel()
        if 'error' in values:
            raise UserError(values['error'])
        self._jetcheckout_cancel_postprocess()

    def jetcheckout_cancel(self):
        self.ensure_one()
        self._jetcheckout_cancel()

    def _jetcheckout_refund(self, amount):
        self.ensure_one()
        if amount > self.amount:
            raise UserError(_('Refund amount cannot be higher than total amount'))
        self._jetcheckout_api_refund(amount)

    def jetcheckout_refund(self):
        self.ensure_one()
        vals = {
            'transaction_id': self.id,
            'total': self.amount,
            'currency_id': self.currency_id.id,
        }
        refund = self.env['payment.acquirer.jetcheckout.refund'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payment.acquirer.jetcheckout.refund',
            'res_id': refund.id,
            'name': _('Create refund for %s') % self.reference,
            'view_mode': 'form',
            'target': 'new',
        }

    def _jetcheckout_process_query(self, vals):
        if vals['successful']:
            if vals['cancelled']:
                self._jetcheckout_cancel_postprocess()
            else:
                self._jetcheckout_done_postprocess()
        else:
            if not self.state == 'error':
                self.write({
                    'state': 'error',
                    'state_message': 'Ödeme başarısız.',
                })

    def _jetcheckout_query(self):
        self.ensure_one()
        values = self._jetcheckout_api_status()
        if 'error' in values:
            raise UserError(values['error'])

        result = values['result']
        vals = {
            'date': result['transaction_date'][:19],
            'name': result['virtual_pos_name'],
            'successful': result['successful'],
            'completed': result['completed'],
            'cancelled': result['cancelled'],
            'threed': result['is_3d'],
            'amount': result['amount'],
            'customer_amount': result['commission_amount'],
            'customer_rate': 100 * result['commission_amount'] / result['amount'] if not result['amount'] == 0 else 0,
            'commission_amount': result['amount'] * result['expected_cost_rate'] / 100,
            'commission_rate': result['expected_cost_rate'],
            'auth_code': result['auth_code'],
            'service_ref_id': result['service_ref_id'],
            'currency_id': self.currency_id.id,
        }
        self._jetcheckout_process_query(result)
        return vals

    def jetcheckout_query(self):
        self.ensure_one()
        vals = self._jetcheckout_query()
        status = self.env['payment.acquirer.jetcheckout.status'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payment.acquirer.jetcheckout.status',
            'res_id': status.id,
            'name': _('%s Transaction Status') % self.reference,
            'view_mode': 'form',
            'target': 'new',
        }

    def _jetcheckout_expire(self):
        self.write({
            'state': 'cancel',
            'state_message': _('Transaction has expired')
        })

    @api.model
    def jetcheckout_expire(self):
        self.sudo().search([
            ('state', 'in', ('draft', 'pending')),
            ('jetcheckout_date_expiration', '!=', False),
            ('jetcheckout_date_expiration', '<', fields.Datetime.now()),
        ])._jetcheckout_expire()
