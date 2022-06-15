# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

import logging
import json
_logger = logging.getLogger(__name__)

class InsufficientCreditError(Exception):
    pass


class ResCompany(models.Model):
    _inherit = 'res.company'

    sms_provider = fields.Selection([], string='SMS Provider')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_provider = fields.Selection(related='company_id.sms_provider', readonly=False)
    sms_test_provider = fields.Boolean(store=False)
    sms_test_message = fields.Char(store=False, readonly=True)

    @api.onchange('sms_provider')
    def onchange_sms_provider(self):
        self.update({
            'sms_test_provider': False,
            'sms_test_message': False,
        })

    @api.onchange('sms_test_provider')
    def onchange_sms_test_provider(self):
        if self.sms_test_provider:
            username = getattr(self, 'sms_%s_username' % self.sms_provider)
            password = getattr(self, 'sms_%s_password' % self.sms_provider)
            message = getattr(self.env['sms.api'], '_get_%s_credit' % self.sms_provider)(username=username, password=password)
            self.update({
                'sms_test_provider': False,
                'sms_test_message': _('Connection is succesful. %s') % message,
            })


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _send_sms(self, numbers, message):
        return self._send_sms_batch([{
            'res_id': 0,
            'number': number,
            'content': message,
        } for number in numbers])

    @api.model
    def _send_sms_batch(self, messages):
        provider = self.env.company.sms_provider
        if provider:
            return getattr(self, '_send_%s_sms' % provider)(messages)
        return super(SmsApi, self)._send_sms_batch(messages)

    @api.model
    def get_credit(self):
        provider = self.env.company.sms_provider
        if provider:
            return getattr(self, '_get_%s_credit' % provider)()
        return False

class SMSResend(models.TransientModel):
    _inherit = 'sms.resend'

    def action_buy_credits(self):
        provider = self.env.company.sms_provider
        if provider:
            url = getattr(self.env['sms.api'], '_get_%s_credit_url' % provider)()
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': url,
            }
        return super().action_buy_credits()
