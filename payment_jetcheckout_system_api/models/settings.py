# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    api_item_notif_mail_create_ok = fields.Boolean(related='company_id.api_item_notif_mail_create_ok', readonly=False)
    api_item_notif_mail_create_template = fields.Many2one(related='company_id.api_item_notif_mail_create_template', readonly=False)
    api_item_notif_sms_create_ok = fields.Boolean(related='company_id.api_item_notif_sms_create_ok', readonly=False)
    api_item_notif_sms_create_template = fields.Many2one(related='company_id.api_item_notif_sms_create_template', readonly=False)
