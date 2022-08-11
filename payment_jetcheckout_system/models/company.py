# -*- coding: utf-8 -*-
from odoo import models, fields

class Company(models.Model):
    _inherit = 'res.company'

    def _compute_is_admin(self):
        for company in self:
            company.is_admin = self.env.user.has_group('base.group_system')

    tax_office = fields.Char()
    system = fields.Selection([])
    is_admin = fields.Boolean(compute='_compute_is_admin', compute_sudo=True)

    def write(self, vals):
        if 'system' in vals and not self.env.user.has_group('base.group_system'):
            del vals['system']
        return super().write(vals)
