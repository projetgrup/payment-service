# -*- coding: utf-8 -*-
from ast import literal_eval
from odoo import api, fields, models, tools


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    company_id = fields.Many2one('res.company')

    @api.model
    def default_get(self, fields):
        res = super(MailTemplate, self).default_get(fields)
        if self.env.company.system:
            res['model_id'] = self.env['ir.model']._get('res.partner').id
            res['company_id'] = self.env.company.id
        return res


class SmsTemplate(models.Model):
    _inherit = 'sms.template'

    company_id = fields.Many2one('res.company')

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
