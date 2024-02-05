# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    @api.depends('company_id')
    def _compute_api_item_notif_mail_create_filter_email_opt(self):
        for setting in self:
            setting.api_item_notif_mail_create_filter_email_opt = 'include' if setting.company_id.api_item_notif_mail_create_filter_email_ok else 'exclude'

    def _set_api_item_notif_mail_create_filter_email_opt(self):
        for setting in self:
            setting.company_id.api_item_notif_mail_create_filter_email_ok = setting.api_item_notif_mail_create_filter_email_opt == 'include'

    @api.depends('company_id')
    def _compute_api_item_notif_sms_create_filter_number_opt(self):
        for setting in self:
            setting.api_item_notif_sms_create_filter_number_opt = 'include' if setting.company_id.api_item_notif_sms_create_filter_number_ok else 'exclude'

    def _set_api_item_notif_sms_create_filter_number_opt(self):
        for setting in self:
            setting.company_id.api_item_notif_sms_create_filter_number_ok = setting.api_item_notif_sms_create_filter_number_opt == 'include'

    api_item_notif_mail_create_ok = fields.Boolean(related='company_id.api_item_notif_mail_create_ok', readonly=False)
    api_item_notif_mail_create_filter_email = fields.Text(related='company_id.api_item_notif_mail_create_filter_email', readonly=False)
    api_item_notif_mail_create_filter_email_ok = fields.Boolean(related='company_id.api_item_notif_mail_create_filter_email_ok', readonly=False)
    api_item_notif_mail_create_filter_email_opt = fields.Selection([('include', 'include'), ('exclude', 'exclude')], compute='_compute_api_item_notif_mail_create_filter_email_opt', inverse='_set_api_item_notif_mail_create_filter_email_opt', string='API Payment Item Email Notification Email Filter Option on Create Request')
    api_item_notif_mail_create_template = fields.Many2one(related='company_id.api_item_notif_mail_create_template', readonly=False)
    api_item_notif_sms_create_ok = fields.Boolean(related='company_id.api_item_notif_sms_create_ok', readonly=False)
    api_item_notif_sms_create_filter_number = fields.Text(related='company_id.api_item_notif_sms_create_filter_number', readonly=False)
    api_item_notif_sms_create_filter_number_ok = fields.Boolean(related='company_id.api_item_notif_sms_create_filter_number_ok', readonly=False)
    api_item_notif_sms_create_filter_number_opt = fields.Selection([('include', 'include'), ('exclude', 'exclude')], compute='_compute_api_item_notif_sms_create_filter_number_opt', inverse='_set_api_item_notif_sms_create_filter_number_opt', string='API Payment Item SMS Notification Number Filter Option on Create Request')
    api_item_notif_sms_create_template = fields.Many2one(related='company_id.api_item_notif_sms_create_template', readonly=False)
