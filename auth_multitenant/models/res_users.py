# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import ustr
from odoo.addons.auth_signup.models.res_partner import SignupError


class ResUsers(models.Model):
    _inherit = 'res.users'

    oauth_ref = fields.Char('OAuth Reference')

    def _default_groups(self):
        template_user = self.env.company.user_template_id
        if template_user.exists():
            return template_user.groups_id
        return super(ResUsers, self)._default_groups()

    def _default_fields(self):
        return [
            'tz',
            'lang',
            'signature',
            'action_id',
            'tz_offset',
            'company_id',
            'company_ids',
            'notification_type',
        ]

    @api.model
    def default_get(self, fields):
        values = super(ResUsers, self).default_get(fields)
        template_user = self.env.company.user_template_id
        if template_user.exists():
            field = self._default_fields()
            value = template_user.read(field, load=None)[0]
            values.update(value)
        return values

    def _create_user_from_template(self, values):
        template_user = self.env.company.user_template_id
        if not template_user.exists():
            return super(ResUsers, self)._create_user_from_template(values)

        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))

        values['active'] = True
        return template_user.with_context(no_reset_password=True).copy(values)
