# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SmsProvider(models.Model):
    _inherit = 'sms.provider'

    type = fields.Selection(selection_add=[('turatel', 'Turatel')], ondelete={'turatel': 'cascade'})


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _get_turatel_credit_url(self):
        return

    @api.model
    def _send_turatel_sms(self, messages, provider):
        is_otp = True #self.env.context.get('otp')
        if provider.syncops_ok and provider.syncops_connector_id:
            for message in messages:
                if message['number']:
                    result, message = self.env['syncops.connector'].sudo()._execute(
                        'sms_post_partner_sms',
                        params={
                            "messages": [message],
                            "originator": provider.originator or '',
                            "isOtp": is_otp,
                        },
                        connectors=provider.syncops_connector_id,
                        message=True,
                    )
                    if result is None:
                        raise ValidationError(message)
            return [{'res_id': message['res_id'], 'state': 'success'} for message in messages]
        else:
            return []

    @api.model
    def _get_turatel_credit(self, provider):
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
            credit = 0
            return _('%s SMS credit(s) left') % int(credit)
