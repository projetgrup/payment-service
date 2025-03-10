# -*- coding: utf-8 -*-
import requests

from odoo import models, fields, api, _


class SmsProvider(models.Model):
    _inherit = 'sms.provider'

    syncops_ok = fields.Boolean(string='Use syncOPS')


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

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
