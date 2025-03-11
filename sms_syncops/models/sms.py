# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SmsProvider(models.Model):
    _inherit = 'sms.provider'

    syncops_ok = fields.Boolean(string='Use syncOPS')
    syncops_connector_id = fields.Many2one('syncops.connector', string='syncOPS Connector')


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _send_sms_api(self, messages, provider):
        provider = self.env['sms.provider'].browse(provider)
        if provider:
            if provider.syncops_ok and provider.syncops_connector_id:
                result, message = self.env['syncops.connector'].sudo()._execute(
                    'sms_post_partner_sms',
                    params={
                        "messages": messages,
                        "originator": provider.originator or '',
                    },
                    connectors=provider.syncops_connector_id,
                    message=True,
                )
                if result is None:
                    raise ValidationError(message)
                return result
            else:
                return getattr(self, '_send_%s_sms' % provider.type, [])(messages, provider)
        return []

    @api.model
    def get_credit(self, provider):
        if provider:
            if provider.syncops_ok and provider.syncops_connector_id:
                result, message = self.env['syncops.connector'].sudo()._execute(
                    'sms_get_partner_sms_credit',
                    params={},
                    connectors=provider.syncops_connector_id,
                    message=True,
                )
                if result is None:
                    raise ValidationError(message)
                return _('%s SMS credit(s) left') % result[0].get('credit', 0)
            else:
                return getattr(self, '_get_%s_credit' % provider.type, _('No SMS provider credit method defined'))(provider)
        return _('No SMS provider defined')
