# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class InsufficientCreditError(Exception):
    pass


class SmsProvider(models.Model):
    _name = 'sms.provider'
    _description = 'SMS Providers'
    _order = 'sequence'
    _rec_name = 'type'

    active = fields.Boolean(default=True)
    sequence = fields.Integer(string='Priority', default=10)
    company_id = fields.Many2one('res.company', ondelete='cascade', string='Company', default=lambda self: self.env.company)
    type = fields.Selection([], string='Provider')
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    originator = fields.Char()

    _sql_constraints = [
        ('company_provider_unique', 'unique (company_id, provider)', 'Provider must be unique per company'),
    ]

    def action_test_connection(self):
        if not self.type:
            raise UserError(_('Please select a provider'))
        message = getattr(self.env['sms.api'], '_get_%s_credit' % self.type)(self)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Connection is succesful. %s') % message,
                'type': 'info',
                'sticky': False,
            }
        }

    @api.model
    def get(self, company=None, type=None, limit=1):
        if not company:
            company = self.env.company.id
        domain = [('company_id', '=', company), ('active', '=', True)]
        if type:
            domain.append(('type', '=', type))
        return self.search(domain, order='sequence', limit=limit)


class SmsSms(models.Model):
    _inherit = 'sms.sms'

    provider_id = fields.Many2one('sms.provider')

    @api.model
    def default_get(self, fields):
        res = super(SmsSms, self).default_get(fields)
        res['provider_id'] = self.provider_id.get().id
        return res

    def _send(self, unlink_failed=False, unlink_sent=True, raise_exception=False):
        data = [{
            'res_id': record.id,
            'number': record.number,
            'content': record.body,
            'provider': record.provider_id.id,
        } for record in self]

        try:
            results = self.env['sms.api']._send_sms_batch(data)
        except Exception as e:
            _logger.error('Sent batch %s SMS: %s: failed with exception %s', len(self.ids), self.ids, e)
            if raise_exception:
                raise
            self._postprocess_iap_sent_sms([{'res_id': sms.id, 'state': 'server_error'} for sms in self], unlink_failed=unlink_failed, unlink_sent=unlink_sent)
        else:
            _logger.info('Send batch %s SMS: %s: gave %s', len(self.ids), self.ids, results)
            self._postprocess_iap_sent_sms(results, unlink_failed=unlink_failed, unlink_sent=unlink_sent)


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _send_sms(self, numbers, message):
        provider = self.env['sms.provider'].get().id
        if not provider:
            return super(SmsApi, self)._send_sms(numbers, message)

        if isinstance(numbers, list):
            vals = [{
                'res_id': 0,
                'number': number,
                'content': message,
                'provider': provider,
            } for number in numbers]
        else:
            vals = [{
                'res_id': 0,
                'number': numbers,
                'content': message,
                'provider': provider,
            }]
        return self._send_sms_batch(vals)

    @api.model
    def _send_sms_batch(self, messages):
        results = []
        providers = {message.get('provider') for message in messages}

        if not all(providers):
            return super(SmsApi, self)._send_sms_batch(messages)

        if not providers:
            return results

        vals = {provider: [] for provider in providers}
        for message in messages:
            vals[message['provider']].append(message)
        for provider, message in vals.items():
            if provider:
                results.extend(self._send_sms_api(messages, provider))
            else:
                results.extend(super(SmsApi, self)._send_sms_batch(messages))
        return results

    @api.model
    def _send_sms_api(self, messages, provider):
        provider = self.env['sms.provider'].browse(provider)
        if provider:
            return getattr(self, '_send_%s_sms' % provider.type, [])(messages, provider)
        return []

    @api.model
    def get_credit(self):
        provider = self.env['sms.provider'].get()
        if provider:
            return getattr(self, '_get_%s_credit' % provider.type, _('No SMS provider credit method defined'))()
        return _('No SMS provider defined')


class SMSResend(models.TransientModel):
    _inherit = 'sms.resend'

    def action_buy_credits(self):
        provider = self.env['sms.provider'].get()
        if provider:
            url = getattr(self.env['sms.api'], '_get_%s_credit_url' % provider.type, '/')()
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': url,
            }
        return super().action_buy_credits()
