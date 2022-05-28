# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Users(models.Model):
    _inherit = 'res.users'

    user_type = fields.Selection([('user','User'),('admin','Administrator')], string='User Type', default='user', required=True)

    @api.model
    def default_get(self, fields):
        values = super(Users, self).default_get(fields)
        template = self.sudo().search([('login','=','sps'),('active','=',False)], limit=1)
        if template:
            values['notification_type'] = template.notification_type
            values['action_id'] = template.action_id
            values['lang'] = template.lang
            values['tz'] = template.tz
        return values

    @api.model_create_multi
    def create(self, vals):
        users = super(Users, self).create(vals)
        if self.env.context.get('is_sps'):
            for user in users:
                user.partner_id.is_sps = True
                if user.user_type == 'user':
                    group = self.env.ref('payment_student.group_sps_user')
                    group.sudo().write({'users': [(4, user.id)]})
                elif user.user_type == 'admin':
                    group = self.env.ref('payment_student.group_sps_manager')
                    group.sudo().write({'users': [(4, user.id)]})
                else:
                    raise ValidationError(_('User type is not valid'))
        return users

    def write(self, vals):
        users = super(Users, self).write(vals)
        if 'user_type' in vals and self.env.context.get('is_sps'):
            group_user = self.env.ref('payment_student.group_sps_user')
            group_admin = self.env.ref('payment_student.group_sps_manager')
            for user in self:
                if user.user_type == 'user':
                    group_user.sudo().write({'users': [(4, user.id)]})
                    group_admin.sudo().write({'users': [(3, user.id)]})
                elif user.user_type == 'admin':
                    group_user.sudo().write({'users': [(3, user.id)]})
                    group_admin.sudo().write({'users': [(4, user.id)]})
                else:
                    raise ValidationError(_('User type is not valid'))
        return users

    def action_reset_password(self):
        if self.env.context.get('is_sps') and self.env.user.has_group('payment_student.group_sps_manager'):
            return super(Users, self.sudo()).action_reset_password()
        return super(Users, self).action_reset_password()
