# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class PaymentSettings(models.TransientModel):
    _name = 'payment.settings'
    _description = 'Payment Settings'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    required_2fa = fields.Boolean(related='company_id.required_2fa', readonly=False)
    notif_mail_success_ok = fields.Boolean(related='company_id.notif_mail_success_ok', readonly=False)
    notif_sms_success_ok = fields.Boolean(related='company_id.notif_sms_success_ok', readonly=False)
    payment_page_campaign_table_ok = fields.Boolean(related='company_id.payment_page_campaign_table_ok', readonly=False)
    notif_webhook_ids = fields.One2many(related='company_id.notif_webhook_ids', readonly=False)
    payment_page_flow = fields.Selection(related='company_id.payment_page_flow', readonly=False)

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

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    url = fields.Char('Url', required=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_default_email_setting = fields.Boolean(string='Payment Default Email Settings', config_parameter='paylox.email.default')
    payment_default_email_server = fields.Many2one('ir.mail_server', string='Payment Default Email Server', config_parameter='paylox.email.server')
    payment_default_email_template = fields.Many2one('mail.template', string='Payment Default Email Template', config_parameter='paylox.email.template')
    payment_default_sms_setting = fields.Boolean(string='Payment Default SMS Settings', config_parameter='paylox.sms.default')
    payment_default_sms_provider = fields.Many2one('sms.provider', string='Payment Default SMS Provider', config_parameter='paylox.sms.provider')
    payment_default_sms_template = fields.Many2one('sms.template', string='Payment Default SMS Settings', config_parameter='paylox.sms.template')
 