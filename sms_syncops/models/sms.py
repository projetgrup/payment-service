# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SmsProvider(models.Model):
    _inherit = 'sms.provider'

    type = fields.Selection(selection_add=[('syncops', 'syncOPS')], ondelete={'syncops': 'cascade'})
    syncops_connector_id = fields.Many2one('syncops.connector', string='syncOPS Connector')
    username = fields.Char(required=False)
    password = fields.Char(required=False)


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _send_syncops_sms(self, messages, provider):
        is_otp = True #self.env.context.get('otp')
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

    @api.model
    def _get_syncops_credit(self, provider):
        result, message = self.env['syncops.connector'].sudo()._execute(
            'sms_get_partner_sms_credit',
            params={},
            connectors=provider.syncops_connector_id,
            message=True,
        )
        if result is None:
            raise ValidationError(message)
        return _('%s SMS credit(s) left') % result[0].get('credit', 0)
