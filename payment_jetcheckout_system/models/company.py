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
    subsystem = fields.Selection([])
    required_2fa = fields.Boolean('Two Factor Required')
    is_admin = fields.Boolean(compute='_compute_is_admin', compute_sudo=True)
    mail_server_id = fields.Many2one('ir.mail_server', compute='_compute_mail_server', compute_sudo=True)

    notif_mail_success_ok = fields.Boolean('Send Successful Payment Transaction Email')
    notif_sms_success_ok = fields.Boolean('Send Successful Payment Transaction SMS')
    notif_webhook_ids = fields.One2many('payment.settings.notification.webhook', 'company_id', 'Webhook URLs')

    payment_page_due_ids = fields.One2many('payment.settings.due', 'company_id', 'Payment Page Dues')
    payment_page_due_ok = fields.Boolean(string='Payment Page Due')
    payment_page_due_base = fields.Selection([
        ('date_due', 'Due Date'),
        ('date_document', 'Document Date'),
    ], string='Payment Page Due Base Date', default='date_due')
    payment_page_flow = fields.Selection([
        ('static', 'Static'),
        ('dynamic', 'Dynamic'),
    ], string='Payment Page Flow', default='static')

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

        res = super().write(vals)
        if 'subsystem' in vals:
            self._update_subsystem()
        return res

    def _update_subsystem(self, users=None):
        for company in self:
            values = []
            if company.system:
                if company.subsystem:
                    system = company.system
                    subsystem = company.subsystem.replace('%s_' % system, '')
                    active_ids = self.env['ir.model.data'].sudo().search_read([
                        ('model', '=', 'res.groups'),
                        ('module', '=', 'payment_%s' % system),
                        ('name', '=', 'group_subsystem_%s' % subsystem)
                    ], ['res_id'], limit=1)
                    values.extend([(4, active_id['res_id']) for active_id in active_ids])

                    inactive_ids = self.env['ir.model.data'].sudo().search_read([
                        ('model', '=', 'res.groups'),
                        ('module', '=', 'payment_%s' % system),
                        ('name', 'like', 'group_subsystem_%'),
                        ('name', '!=', 'group_subsystem_%s' % subsystem),
                    ], ['res_id'])
                    values.extend([(3, inactive_id['res_id']) for inactive_id in inactive_ids])

                else:
                    inactive_ids = self.env['ir.model.data'].sudo().search_read([
                        ('model', '=', 'res.groups'),
                        ('module', '=', 'payment_%s' % company.system),
                        ('name', 'like', 'group_subsystem_%')
                    ], ['res_id'])
                    values.extend([(3, inactive_id['res_id']) for inactive_id in inactive_ids])
            else:
                inactive_ids = self.env['ir.model.data'].sudo().search_read([
                    ('model', '=', 'res.groups'),
                    ('module', 'like', 'payment_%'),
                    ('name', 'like', 'group_subsystem_%')
                ], ['res_id'])
                values.extend([(3, inactive_id['res_id']) for inactive_id in inactive_ids])

            if values:
                if not users:
                    users = self.env['res.users'].sudo().with_context(active_test=False).search([
                        ('share', '=', False),
                        ('company_id', '=', company.id),
                    ])
                users.write({'groups_id': values})
