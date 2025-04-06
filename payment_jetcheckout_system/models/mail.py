# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    company_id = fields.Many2one('res.company')
    system = fields.Boolean()

    @api.model
    def default_get(self, fields):
        res = super(MailTemplate, self).default_get(fields)
        if self.env.company.system:
            res['model_id'] = self.env['ir.model']._get('res.partner').id
            res['company_id'] = self.env.company.id
        return res

class MailMessage(models.Model):
    _inherit = 'mail.message'

    def _compute_mail_state(self):
        for message in self:
            if message.mail_ids:
                if any(m.state == 'sent' for m in message.mail_ids):
                    message.mail_state = 'sent'
                else:
                    message.mail_state = message.mail_ids[0].state
            else:
                message.mail_state = False

    mail_state = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('exception', 'Failed'),
        ('cancel', 'Cancelled'),
    ], string='Email State', compute='_compute_mail_state')


class SmsTemplate(models.Model):
    _inherit = 'sms.template'

    company_id = fields.Many2one('res.company')
    system = fields.Boolean()

    @api.model
    def default_get(self, fields):
        res = super(SmsTemplate, self).default_get(fields)
        if self.env.company.system:
            res['model_id'] = self.env['ir.model']._get('res.partner').id
            res['company_id'] = self.env.company.id
        return res


class MailServer(models.Model):
    _inherit = 'ir.mail_server'

    @api.depends('company_id', 'email')
    def _compute_email_formatted(self):
        for server in self:
            if server.email:
                server.email_formatted = tools.formataddr((server.company_id.name or u"False", server.email or u"False"))
            else:
                server.email_formatted = ''

    company_id = fields.Many2one('res.company')
    email = fields.Char('Default Email Address')
    email_formatted = fields.Char(string='Formatted Default Email Address', compute="_compute_email_formatted")

    @api.model
    def default_get(self, fields):
        res = super(MailServer, self).default_get(fields)
        if self.env.company.system:
            res['company_id'] = self.env.company.id
        return res


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def create(self, values):
        company = self.env.company
        if company.system:
            self = self.with_context(mail_notracking=True)
        return super(MailThread, self).create(values)

    def write(self, values):
        company = self.env.company
        if company.system:
            self = self.with_context(mail_notracking=True)
        return super(MailThread, self).write(values)

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        if self.env.context.get('mail_notracking'):
            return []
        return super(MailThread, self)._message_auto_subscribe_followers(updated_values, default_subtype_ids)
