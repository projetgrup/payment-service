# -*- coding: utf-8 -*-
from odoo import models, fields


class Users(models.Model):
    _inherit = 'res.users'

    def _compute_group_syncops_sync(self):
        for user in self:
            user.group_syncops_sync = user.has_group('payment_syncops.group_sync')

    def _set_group_syncops_sync(self):
        for user in self:
            code = user.group_syncops_sync and 4 or 3
            group = self.env.ref('payment_syncops.group_sync')
            group.sudo().write({'users': [(code, user.id)]})

    group_syncops_sync = fields.Boolean(string='syncOPS Sync', compute='_compute_group_syncops_sync', inverse='_set_group_syncops_sync')
