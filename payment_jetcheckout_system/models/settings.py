# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class PaymentSettings(models.TransientModel):
    _name = 'payment.settings'
    _description = 'Payment Settings'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    notif_webhook_ids = fields.One2many(related='company_id.notif_webhook_ids', readonly=False)

    def start(self):
        return self.next()

    def copy(self, values):
        raise UserError(_('Cannot duplicate configuration!'), '')

    def next(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def execute(self):
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


class PaymentSettingsNotificationWebhook(models.Model):
    _name = 'payment.settings.notification.webhook'
    _description = 'Payment Settings Notification Webhook'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    url = fields.Char('Url', required=True)
