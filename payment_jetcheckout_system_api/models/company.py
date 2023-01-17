# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    api_item_notif_mail_create_ok = fields.Boolean(string='API Payment Item Email Notification on Create Request')
    api_item_notif_mail_create_template = fields.Many2one('mail.template', string='API Payment Item Email Notification Template on Create Request')
    api_item_notif_sms_create_ok = fields.Boolean(string='API Payment Item SMS Notification on Create Request')
    api_item_notif_sms_create_template = fields.Many2one('sms.template', string='API Payment Item SMS Notification Template on Create Request')
