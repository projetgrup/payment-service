# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import frozendict
from odoo.exceptions import AccessDenied


class Users(models.Model):
    _inherit = 'res.users'

    def _compute_privilege(self):
        for user in self:
            system = user.company_id.system or 'jetcheckout_system'
            if user.has_group('payment_%s.group_%s_manager' % (system, system)):
                user.privilege = 'admin'
            elif user.has_group('payment_%s.group_%s_user' % (system, system)):
                user.privilege = 'user'
            else:
                user.privilege = ''

    def _set_privilege(self):
        for user in self:
            system = user.company_id.system
            module = system or 'jetcheckout_system'
            name = system or 'system'
            group_user = self.env.ref('payment_%s.group_%s_user' % (module, name))
            group_admin = self.env.ref('payment_%s.group_%s_manager' % (module, name))
            if user.privilege == 'admin':
                group_user.sudo().write({'users': [(4, user.id)]})
                group_admin.sudo().write({'users': [(4, user.id)]})
            elif user.privilege == 'user':
                group_user.sudo().write({'users': [(4, user.id)]})
                group_admin.sudo().write({'users': [(3, user.id)]})
            else:
                group_user.sudo().write({'users': [(3, user.id)]})
                group_admin.sudo().write({'users': [(3, user.id)]})

    def _compute_group_transaction_commission(self):
        for user in self:
            user.group_transaction_commission = user.has_group('payment_jetcheckout.group_transaction_commission')

    def _set_group_transaction_commission(self):
        for user in self:
            code = user.group_transaction_commission and 4 or 3
            group = self.env.ref('payment_jetcheckout.group_transaction_commission')
            group.sudo().write({'users': [(code, user.id)]})

    privilege = fields.Selection([('user','User'),('admin','Administrator')], string='Privilege Type', compute='_compute_privilege', inverse='_set_privilege')
    group_transaction_commission = fields.Boolean(string='Transaction Commissions', compute='_compute_group_transaction_commission', inverse='_set_group_transaction_commission')

    def _check_token(self, token):
        id, token = self.partner_id._resolve_token(token)
        if not self.partner_id.id == id or not self.partner_id.access_token == token:
            raise AccessDenied()

    def _check_credentials(self, password, env):
        env = env or {}
        if env.get('token', False):
            return self._check_token(env['token'])
        return super()._check_credentials(password, env)

    @classmethod
    def authenticate(cls, db, login, password, env):
        if isinstance(password, dict):
            if password['token']:
                env = env or {}
                env['token'] = password['token']
                password = password['token']
        return super(Users, cls).authenticate(db, login, password, env)

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
