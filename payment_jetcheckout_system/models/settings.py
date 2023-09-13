# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError


class PaymentSettings(models.TransientModel):
    _name = 'payment.settings'
    _description = 'Payment Settings'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    required_2fa = fields.Boolean(related='company_id.required_2fa', readonly=False)

    payment_page_flow = fields.Selection(related='company_id.payment_page_flow', readonly=False)
    payment_page_campaign_table_ok = fields.Boolean(related='company_id.payment_page_campaign_table_ok', readonly=False)
    payment_page_due_ok = fields.Boolean(related='company_id.payment_page_due_ok', readonly=False)
    payment_page_due_ids = fields.One2many(related='company_id.payment_page_due_ids', readonly=False)
    payment_page_due_base = fields.Selection(related='company_id.payment_page_due_base', readonly=False)

    notif_mail_success_ok = fields.Boolean(related='company_id.notif_mail_success_ok', readonly=False)
    notif_sms_success_ok = fields.Boolean(related='company_id.notif_sms_success_ok', readonly=False)
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
        return self.next()

    def cancel(self):
        return self.refresh()

    def refresh(self):
        actions = self.env['ir.actions.act_window'].sudo().search([('res_model', '=', self._name)], limit=1)
        if actions:
            return actions.read()[0]
        return {}

    def name_get(self):
        action = self.env['ir.actions.act_window'].sudo().search([('res_model', '=', self._name)], limit=1)
        name = action.name or self._name
        return [(record.id, name) for record in self]


class PaymentSettingsNotificationWebhook(models.Model):
    _name = 'payment.settings.notification.webhook'
    _description = 'Payment Settings Notification Webhook'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    url = fields.Char('URL', required=True)

class PaymentSettingsDue(models.Model):
    _name = 'payment.settings.due'
    _description = 'Payment Settings Dues'

    @api.model
    def _get_acquirers(self, partner=None, limit=None):
        company = partner and partner.company_id or self.env.company
        return self.env['payment.acquirer'].sudo()._get_acquirer(company=company, providers=['jetcheckout'], limit=limit, raise_exception=False)

    @api.onchange('due')
    def _compute_unit(self):
        for line in self:
            if line.due > 1:
                line.unit = _('Days')
            else:
                line.unit = _('Day')

    @api.onchange('due')
    def _compute_campaign_ids(self):
        for line in self:
            acquirers = self._get_acquirers()
            campaigns = acquirers.mapped('paylox_campaign_ids')
            line.campaign_ids = [(6, 0, campaigns.ids)]

    def _default_campaign_id(self):
        acquirers = self._get_acquirers(limit=1)
        if acquirers:
            return acquirers.jetcheckout_campaign_id.id
        return False

    due = fields.Integer('Due', default=0, required=True)
    tolerance = fields.Integer('Tolerance', default=0, required=True)
    unit = fields.Char('Unit', compute='_compute_unit')
    round = fields.Boolean('Round')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    campaign_id = fields.Many2one('payment.acquirer.jetcheckout.campaign', string='Campaign', ondelete='set null', domain='[("id", "in", campaign_ids)]', default=_default_campaign_id)
    campaign_ids = fields.Many2many('payment.acquirer.jetcheckout.campaign', 'Campaigns', compute='_compute_campaign_ids')

    def get_campaign(self, day):
        for due in self:
            rounding_method = 'HALF-UP' if due.round else 'DOWN'
            days = float_round(day, precision_digits=0, rounding_method=rounding_method)
            if due.due - due.tolerance >= days:
                return days, due.campaign_id.name or ''
        
        days = float_round(day, precision_digits=0)
        return days, ''


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_default_email_setting = fields.Boolean(string='Payment Default Email Settings', config_parameter='paylox.email.default')
    payment_default_email_server = fields.Many2one('ir.mail_server', string='Payment Default Email Server', config_parameter='paylox.email.server')
    payment_default_email_template = fields.Many2one('mail.template', string='Payment Default Email Template', config_parameter='paylox.email.template')
    payment_default_sms_setting = fields.Boolean(string='Payment Default SMS Settings', config_parameter='paylox.sms.default')
    payment_default_sms_provider = fields.Many2one('sms.provider', string='Payment Default SMS Provider', config_parameter='paylox.sms.provider')
    payment_default_sms_template = fields.Many2one('sms.template', string='Payment Default SMS Settings', config_parameter='paylox.sms.template')
 