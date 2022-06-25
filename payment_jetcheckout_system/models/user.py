# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import frozendict


class Users(models.Model):
    _inherit = 'res.users'

    def _compute_privilege(self):
        for user in self:
            system = user.company_id.system
            if system:
                if user.has_group('payment_%s.group_%s_manager' % (system, system)):
                    user.privilege = 'admin'
                elif user.has_group('payment_%s.group_%s_user' % (system, system)):
                    user.privilege = 'user'
                else:
                    user.privilege = ''
            else:
                user.privilege = ''

    def _set_privilege(self):
        for user in self:
            system = user.company_id.system
            if system:
                group_user = self.env.ref('payment_%s.group_%s_user' % (system, system))
                group_admin = self.env.ref('payment_%s.group_%s_manager' % (system, system))
                if user.privilege == 'admin':
                    group_user.sudo().write({'users': [(4, user.id)]})
                    group_admin.sudo().write({'users': [(4, user.id)]})
                elif user.privilege == 'user':
                    group_user.sudo().write({'users': [(4, user.id)]})
                    group_admin.sudo().write({'users': [(3, user.id)]})
                else:
                    group_user.sudo().write({'users': [(3, user.id)]})
                    group_admin.sudo().write({'users': [(3, user.id)]})
            else:
                group_user = self.env.ref('payment_jetcheckout_system.group_system_user')
                group_admin = self.env.ref('payment_jetcheckout_system.group_system_manager')
                group_user.sudo().write({'users': [(3, user.id)]})
                group_admin.sudo().write({'users': [(3, user.id)]})

    privilege = fields.Selection([('user','User'),('admin','Administrator')], string='Privilege Type', compute='_compute_privilege', inverse='_set_privilege')

    @api.model
    def default_get(self, fields):
        values = super(Users, self).default_get(fields)
        system = self.env.company.system
        if system:
            template = self.sudo().search([('login','=',system),('active','=',False)], limit=1)
            if template:
                values['notification_type'] = template.notification_type
                values['action_id'] = template.action_id
                values['lang'] = template.lang
                values['tz'] = template.tz
        return values

    def write(self, vals):
        users = super(Users, self).write(vals)
        for user in self:
            system = user.company_id.system
            if 'company_id' in vals:
                user.partner_id.company_id = system and user.company_id.id or False
        return users

    def context_get(self):
        ctx = super(Users, self).context_get()
        context = dict(ctx)
        context['system'] = self.env.context.get('system')
        return frozendict(context)

    def action_reset_password(self):
        if self.company_id.system:
            return super(Users, self.sudo()).action_reset_password()
        return super(Users, self).action_reset_password()
