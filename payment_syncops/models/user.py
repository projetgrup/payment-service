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

    def _compute_group_syncops_check_iban(self):
        for user in self:
            user.group_syncops_check_iban = user.has_group('payment_syncops.group_check_iban')

    def _set_group_syncops_check_iban(self):
        for user in self:
            code = user.group_syncops_check_iban and 4 or 3
            group = self.env.ref('payment_syncops.group_check_iban')
            group.sudo().write({'users': [(code, user.id)]})
    
    def _compute_group_syncops_check_card(self):
        for user in self:
            user.group_syncops_check_card = user.has_group('payment_syncops.group_check_card')

    def _set_group_syncops_check_card(self):
        for user in self:
            code = user.group_syncops_check_card and 4 or 3
            group = self.env.ref('payment_syncops.group_check_card')
            group.sudo().write({'users': [(code, user.id)]})
    
    group_syncops_sync = fields.Boolean(string='syncOPS Sync', compute='_compute_group_syncops_sync', inverse='_set_group_syncops_sync')
    group_syncops_check_iban = fields.Boolean(string='syncOPS Check IBAN', compute='_compute_group_syncops_check_iban', inverse='_set_group_syncops_check_iban')
    group_syncops_check_card = fields.Boolean(string='syncOPS Check Credit Card Number', compute='_compute_group_syncops_check_card', inverse='_set_group_syncops_check_card')
