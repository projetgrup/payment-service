# -*- coding: utf-8 -*-
from ast import literal_eval
from odoo import api, fields, models


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

    company_id = fields.Many2one('res.company')

    @api.model
    def default_get(self, fields):
        res = super(MailServer, self).default_get(fields)
        if self.env.company.system:
            res['company_id'] = self.env.company.id
        return res


class Mailing(models.Model):
    _inherit = 'mailing.mailing'

    @api.depends('mailing_domain')
    def _compute_partner_ids(self):
        for mail in self:
            mail.partner_ids = self.env['res.partner'].sudo().search(literal_eval(self.mailing_domain))

    company_id = fields.Many2one('res.company')
    partner_ids = fields.Many2many('res.partner', compute='_compute_partner_ids', store=True)

    @api.model
    def default_get(self, fields):
        res = super(Mailing, self).default_get(fields)
        res['company_id'] = self.env.company.id
        return res


class UtmSource(models.Model):
    _inherit = 'utm.source'

    def write(self, vals):
        if self.env.context.get('readonly'):
            return
        return super().write(vals)
