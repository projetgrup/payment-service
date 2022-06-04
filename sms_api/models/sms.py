# -*- coding: utf-8 -*-
import requests
from odoo import models, fields, api

class InsufficientCreditError(Exception):
    pass

class ResCompany(models.Model):
    _inherit = 'res.company'

    sms_provider = fields.Selection([], string='SMS Provider')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_provider = fields.Selection(related='company_id.sms_provider', readonly=False)

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
