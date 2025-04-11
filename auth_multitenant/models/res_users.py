# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.tools.misc import ustr
from odoo.addons.auth_signup.models.res_partner import SignupError

import logging
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _create_user_from_template(self, values):
        template_user = self.env.company.user_template_id
        if not template_user.exists():
            return super(ResUsers, self)._create_user_from_template(values)

        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))

        values['active'] = True
        try:
            with self.env.cr.savepoint():
                return template_user.with_context(no_reset_password=True).copy(values)
        except Exception as e:
            raise SignupError(ustr(e))
