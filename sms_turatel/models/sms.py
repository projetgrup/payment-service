# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


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
        return []

    @api.model
    def _get_turatel_credit(self, provider):
        credit = 0
        return _('%s SMS credit(s) left') % int(credit)
