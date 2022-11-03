# -*- coding: utf-8 -*-
from odoo import models, fields

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
    is_admin = fields.Boolean(compute='_compute_is_admin', compute_sudo=True)
    mail_server_id = fields.Many2one('ir.mail_server', compute='_compute_mail_server', compute_sudo=True)

    def write(self, vals):
        if 'system' in vals and not self.env.user.has_group('base.group_system'):
            del vals['system']
        return super().write(vals)
