# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Company(models.Model):
    _inherit = 'res.company'

    def _compute_is_admin(self):
        for company in self:
            company.is_admin = self.env.user.has_group('base.group_system')

    def _compute_mail_server(self):
        for company in self:
            company.mail_server_id = self.env['ir.mail_server'].search([('company_id', '=', company.id)], limit=1).id

    tax_office = fields.Char()
    system = fields.Selection([])
    required_2fa = fields.Boolean('Two Factor Required')
    notif_mail_success_ok = fields.Boolean('Send Successful Payment Transaction Email')
    notif_sms_success_ok = fields.Boolean('Send Successful Payment Transaction SMS')
    is_admin = fields.Boolean(compute='_compute_is_admin', compute_sudo=True)
    mail_server_id = fields.Many2one('ir.mail_server', compute='_compute_mail_server', compute_sudo=True)
    notif_webhook_ids = fields.One2many('payment.settings.notification.webhook', 'company_id', 'Webhook URLs')

    @api.model
    def create(self, vals):
        company = super(Company, self.with_context(skip_company=True)).create(vals)
        if 'system' in vals:
            company.partner_id.write({
                'company_id': company.id,
                'system': vals['system'],
            })
        return company

    def write(self, vals):
        if 'system' in vals:
            if self.env.user.has_group('base.group_system'):
                for company in self:
                    company.partner_id.write({
                        'company_id': company.id,
                        'system': vals['system'],
                    })
            else:
                del vals['system']
        return super().write(vals)
