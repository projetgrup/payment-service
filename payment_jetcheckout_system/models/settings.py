# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import json


class PaymentSettings(models.TransientModel):
    _name = 'payment.settings'
    _description = 'Payment Settings'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    sms_provider = fields.Selection(related='company_id.sms_provider', readonly=False, default=lambda self: self.env.company.sms_provider)
    sms_username = fields.Char()
    sms_password = fields.Char()
    sms_originator = fields.Char()
    sms_test_provider = fields.Boolean(store=False)
    sms_test_message = fields.Char(store=False, readonly=True)

    def start(self):
        return self.next()

    def copy(self, values):
        raise UserError(_('Cannot duplicate configuration!'), '')

    def next(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.onchange('sms_provider')
    def onchange_sms_provider(self):
        company = self.company_id
        provider = self.sms_provider
        if provider:
            self.update({
                'sms_username': getattr(company, 'sms_%s_username' % provider),
                'sms_password': getattr(company, 'sms_%s_password' % provider),
                'sms_originator': getattr(company, 'sms_%s_originator' % provider),
            })

        self.update({
            'sms_test_provider': False,
            'sms_test_message': False,
        })

    @api.onchange('sms_test_provider')
    def onchange_sms_test_provider(self):
        if self.sms_test_provider:
            username = self.sms_username
            password = self.sms_password
            message = getattr(self.env['sms.api'], '_get_%s_credit' % self.sms_provider)(username=username, password=password)
            self.sms_test_provider = False
            self.update({
                'sms_test_provider': False,
                'sms_test_message': _('Connection is succesful. %s') % message,
            })

    def set_values(self):
        company = self.company_id
        provider = self.sms_provider
        if provider:
            company.write({
                'sms_%s_username' % provider: self.sms_username,
                'sms_%s_password' % provider: self.sms_password,
                'sms_%s_originator' % provider: self.sms_originator
            })

    def execute(self):
        self.set_values()
        return self.refresh()

    def cancel(self):
        return self.refresh()

    def refresh(self):
        actions = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
        if actions:
            return actions.read()[0]
        return {}

    def name_get(self):
        action = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
        name = action.name or self._name
        return [(record.id, name) for record in self]
