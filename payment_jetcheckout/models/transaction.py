# -*- coding: utf-8 -*-
import requests
import logging
import json

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError, ValidationError, AccessError

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

    partner_vat = fields.Char(string='VAT')
    state = fields.Selection(selection_add=[('expired', 'Expired')], ondelete={'expired': lambda recs: recs.write({'state': 'cancel'})})
    is_jetcheckout = fields.Boolean(compute='_calc_is_jetcheckout')
    jetcheckout_payment_ok = fields.Boolean('Payment Required', readonly=True, copy=False, default=True)
    jetcheckout_campaign_name = fields.Char('Campaign Name', readonly=True, copy=False)
    jetcheckout_card_name = fields.Char('Card Holder Name', readonly=True, copy=False)
    jetcheckout_card_number = fields.Char('Card Number', readonly=True, copy=False)
    jetcheckout_card_type = fields.Char('Card Type', readonly=True, copy=False)
    jetcheckout_card_family = fields.Char('Card Family', readonly=True, copy=False)
    jetcheckout_vpos_id = fields.Integer('Virtual PoS Id', readonly=True, copy=False)
    jetcheckout_vpos_name = fields.Char('Virtual PoS', readonly=True, copy=False)
    jetcheckout_vpos_ref = fields.Char('Virtual PoS Reference', readonly=True, copy=False)
    jetcheckout_vpos_code = fields.Char('Virtual PoS Code', readonly=True, copy=False)
    jetcheckout_order_id = fields.Char('Order', readonly=True, copy=False)
    jetcheckout_ip_address = fields.Char('IP Address', readonly=True, copy=False)
    jetcheckout_transaction_id = fields.Char('Transaction', readonly=True, copy=False)
    jetcheckout_payment_amount = fields.Monetary('Payment Amount', readonly=True, copy=False)
    jetcheckout_installment_count = fields.Integer('Installment Count', readonly=True, copy=False)
    jetcheckout_installment_plus = fields.Integer('Plus Installment Count', readonly=True, copy=False)
    jetcheckout_installment_description = fields.Char('Installment Description', readonly=True, copy=False)
    jetcheckout_installment_description_long = fields.Char('Installment Long Description', readonly=True, compute='_calc_installment_description_long')
    jetcheckout_installment_amount = fields.Monetary('Installment Amount', readonly=True, copy=False)
    jetcheckout_commission_rate = fields.Float('Commission Rate', readonly=True, copy=False)
    jetcheckout_commission_amount = fields.Monetary('Commission Amount', readonly=True, copy=False)
    jetcheckout_customer_rate = fields.Float('Customer Commission Rate', readonly=True, copy=False)
    jetcheckout_customer_amount = fields.Monetary('Customer Commission Amount', readonly=True, copy=False)
    jetcheckout_website_id = fields.Many2one('website', 'Website', readonly=True, copy=False)
    jetcheckout_date_expiration = fields.Datetime('Expiration Date', readonly=True, copy=False)

    @api.model
    def _compute_reference(self, provider, prefix=None, separator='-', **kwargs):
        if provider == 'jetcheckout':
            sequence = 'payment.jetcheckout.transaction'
            reference = self.env['ir.sequence'].sudo().next_by_code(sequence)
            if not reference:
                raise ValidationError(_('You have to define a sequence for %s') % sequence)
            return reference
        return super()._compute_reference(provider, prefix=prefix, separator=separator, **kwargs) 

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

    def unlink(self):
        for tx in self:
            if tx.state not in ('draft', 'pending'):
                raise ValidationError(_('Only "Draft" or "Pending" payment transactions can be removed'))
        return super().unlink()

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

    def _jetcheckout_payment(self, values={}, raise_exception=False):
        if self.payment_id:
            return False

        if not self.jetcheckout_payment_ok:
            self.write({'jetcheckout_payment_ok': True})

        line = self.env.context.get('journal_line') or self.acquirer_id.sudo()._get_journal_line(self.jetcheckout_vpos_name, self.jetcheckout_vpos_ref)
        if not line:
            message = _('There is no journal line for %s in %s (%s)') % (self.jetcheckout_vpos_name, self.acquirer_id.name, self.reference)
            if raise_exception:
                raise ValidationError(message)
            self.write({'state_message': message})
            return False

        if not line.journal_id:
            message = _('There is no journal for %s in %s (%s)') % (self.jetcheckout_vpos_name, self.acquirer_id.name, self.reference)
            if raise_exception:
                raise ValidationError(message)
            self.write({'state_message': message})
            return False

        payment_method = self.env.ref('payment_jetcheckout.payment_method_jetcheckout')
        payment_method_line = line.journal_id.inbound_payment_method_line_ids.filtered(lambda x: x.payment_method_id.id == payment_method.id)
        if not payment_method_line:
            message = _('Jetcheckout payment method has not been set yet on inbound payment methods of journal %s.' % line.journal_id.name)
            if raise_exception:
                raise ValidationError(message)
            self.write({'state_message': message})
            return False

        payment = self.env['account.payment'].with_context(line=line, skip_account_move_synchronization=True).create({
            'amount': abs(self.amount),
            'partner_id': self.partner_id.commercial_partner_id.id,
            'journal_id': line.journal_id.id,
            'payment_method_line_id': payment_method_line.id,
            'payment_token_id': self.token_id.id,
            'payment_transaction_id': self.id,
            'ref': self.reference,
            **values
        })
        self.write({'payment_id': payment.id})

        if not self.env.context.get('post_later'):
            payment.post_with_jetcheckout(line, self.jetcheckout_customer_amount, self.jetcheckout_ip_address)
        return payment

    def _jetcheckout_refund_postprocess_values(self):
        return {
            'jetcheckout_card_name': self.jetcheckout_card_name,
            'jetcheckout_card_number': self.jetcheckout_card_number,
            'jetcheckout_card_type': self.jetcheckout_card_type,
            'jetcheckout_card_family': self.jetcheckout_card_family,
            'jetcheckout_vpos_id': self.jetcheckout_vpos_id,
            'jetcheckout_vpos_name': self.jetcheckout_vpos_name,
            'is_post_processed': True,
            'state': 'done',
            'state_message': _('Transaction has been refunded successfully.'),
            'last_state_change': fields.Datetime.now(),
        }

    def _jetcheckout_refund_postprocess(self, amount=None):
        transaction = self._create_refund_transaction(amount_to_refund=amount, **self._jetcheckout_refund_postprocess_values())
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
        if self.state == 'cancel':
            return {}

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

    def _jetcheckout_done_postprocess_values(self):
        return {
            'state': 'done',
            'is_post_processed': True,
            'last_state_change': fields.Datetime.now(),
            'state_message': _('Transaction is successful.'),
        }

    def _jetcheckout_done_postprocess(self):
        self.write(self._jetcheckout_done_postprocess_values())
        self.jetcheckout_order_confirm()
        self.jetcheckout_payment()

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
        if not self.jetcheckout_payment_ok:
            return

        try:
            self.env.cr.commit()
            payment = self.sudo()._jetcheckout_payment()
            if payment:
                if self.invoice_ids:
                    self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
                    (payment.line_ids + self.invoice_ids.line_ids).filtered(lambda line: line.account_id == payment.destination_account_id and not line.reconciled).reconcile()
                self.write({
                    'state_message': _('Transaction is succesful and payment has been validated.'),
                })
            else:
                if not self.state_message:
                    self.write({
                        'state_message': _('Transaction is succesful.'),
                    })
        except Exception as e:
            self.env.cr.rollback()
            self.write({
                'state_message': _('Transaction is succesful, but payment could not be validated. Probably one of partner or journal accounts are missing.') + '\n' + str(e),
            })
            _logger.warning('Creating payment for transaction %s is failed\n%s' % (self.reference, e))

    def _jetcheckout_cancel_postprocess_values(self):
        return {
            'state': 'cancel',
            'state_message': _('Transaction has been cancelled successfully.'),
            'last_state_change': fields.Datetime.now(),
        }

    def _jetcheckout_cancel_postprocess(self):
        if not self.state == 'cancel':
            self.write(self._jetcheckout_cancel_postprocess_values())

    def _jetcheckout_cancel(self):
        self.ensure_one()
        if not self.state == 'cancel':
            if not self.state in ('draft', 'pending'):
                values = self._jetcheckout_api_cancel()
                if 'error' in values:
                    raise UserError(values['error'])
            self._jetcheckout_cancel_postprocess()

    def jetcheckout_cancel(self):
        self.ensure_one()
        if not self.env.user.has_group('payment_jetcheckout.group_transaction_cancel'):
            raise AccessError(_('You do not have any permission to cancel this transaction'))
 
        self._jetcheckout_cancel()

    def _jetcheckout_refund(self, amount):
        self.ensure_one()
        if amount > self.amount:
            raise UserError(_('Refund amount cannot be higher than total amount'))
        self._jetcheckout_api_refund(amount)

    def jetcheckout_refund(self):
        self.ensure_one()
        if not self.env.user.has_group('payment_jetcheckout.group_transaction_refund'):
            raise AccessError(_('You do not have any permission to refund this transaction'))

        refunds = self.search([('source_transaction_id', '=', self.id)])
        vals = {
            'transaction_id': self.id,
            'total': self.amount + sum(refunds.mapped('amount')),
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

    def _jetcheckout_process_query(self, values):
        if 'commission_amount' not in values:
            values['commission_amount'] = float_round(self.amount * values['commission_rate'] / 100, 2)

        self.write({
            'fees': values['commission_amount'],
            'jetcheckout_vpos_id': values['vpos_id'],
            'jetcheckout_vpos_name': values['vpos_name'],
            'jetcheckout_vpos_ref': values['vpos_ref'],
            'jetcheckout_vpos_code': values['vpos_code'],
            'jetcheckout_payment_amount': self.jetcheckout_payment_amount or self.amount - self.jetcheckout_customer_amount,
            'jetcheckout_commission_rate': values['commission_rate'],
            'jetcheckout_commission_amount': values['commission_amount'],
            'jetcheckout_card_family': values['card_family'],
            'jetcheckout_card_type': values['card_program'],
            'jetcheckout_card_number': self.jetcheckout_card_number or '%s**********' % values['bin_code'],
        })

        if values['successful']:
            if 'cancelled' in values and values['cancelled']:
                self._jetcheckout_cancel_postprocess()
            else:
                self._jetcheckout_done_postprocess()
        else:
            if self.state == 'error' or self.env.context.get('skip_error'):
                return
            else:
                self.write({
                    'state': 'error',
                    'state_message': _('%s (Error Code: %s)') % (values.get('message', '-'), values.get('code','')),
                    'last_state_change': fields.Datetime.now(),
                })

    def _jetcheckout_query(self, values={}):
        self.ensure_one()
        if not values:
            values = self._jetcheckout_api_status()
            if 'error' in values:
                raise UserError(values['error'])

            result = values['result']
            commission_rate = result['expected_cost_rate']
            commission_amount = float_round(self.amount * commission_rate / 100, 2)
            values = {
                'date': result['transaction_date'][:19],
                'vpos_id': result['virtual_pos_id'],
                'vpos_name': result['virtual_pos_name'],
                'vpos_ref': result['pos_bank_eft_code'] or result['card_bank_eft_code'],
                'vpos_code': result['auth_code'],
                'successful': result['successful'],
                'completed': result['completed'],
                'cancelled': result['cancelled'],
                'threed': result['is_3d'],
                'auth_code': result['auth_code'],
                'card_family': result['card_family'] and result['card_family'].lower().capitalize() or '',
                'card_program': result['card_program'] and result['card_program'].lower().capitalize() or '',
                'bin_code': result['bin_code'],
                'service_ref_id': result['service_ref_id'],
                'amount': self.amount,
                'commission_amount': commission_amount,
                'commission_rate': commission_rate,
                'customer_amount': self.jetcheckout_customer_amount,
                'customer_rate': self.jetcheckout_customer_rate,
                'currency_id': self.currency_id.id,
            }

        self._jetcheckout_process_query(values)
        return values

    def jetcheckout_query(self):
        self.ensure_one()
        values = self._jetcheckout_query()
        status = self.env['payment.acquirer.jetcheckout.status'].create(values)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payment.acquirer.jetcheckout.status',
            'res_id': status.id,
            'name': _('%s Transaction Status') % self.reference,
            'view_mode': 'form',
            'target': 'new',
        }

    def _jetcheckout_expire(self):
        self.filtered(lambda x: x.state in ('draft', 'pending')).write({
            'state': 'expired',
            'state_message': _('Transaction has expired'),
            'last_state_change': fields.Datetime.now(),
        })

    @api.model
    def jetcheckout_expire(self):
        self.sudo().search([
            ('state', 'in', ('draft', 'pending')),
            ('jetcheckout_date_expiration', '!=', False),
            ('jetcheckout_date_expiration', '<', fields.Datetime.now()),
        ])._jetcheckout_expire()

    @api.model
    def jetcheckout_fix(self, companies=None, states=None):
        """
        Use this function in case of emergency when transaction records are corrupted.
        It requests data from payment service and resync related transactions.
        """
        if not companies or not states:
            return

        txs = self.sudo().search([('company_id', 'in', companies), ('state', 'in', states)])
        for tx in txs:
            try:
                tx._jetcheckout_query()
                self.env.cr.commit()
            except:
                self.cr.rollback()
