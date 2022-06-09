# -*- coding: utf-8 -*-
from odoo import models

class Partner(models.Model):
    _inherit = 'res.partner'

    def action_grant_access(self):
        self.ensure_one()
        self._assert_user_email_uniqueness()

        if self.is_portal or self.is_internal:
            return

        group_portal = self.env.ref('base.group_portal')
        group_public = self.env.ref('base.group_public')

        if self.partner_id.email != self.email:
            self.partner_id.write({'email': self.email})

        user_sudo = self.user_id.sudo()

        if not user_sudo:
            company = self.partner_id.company_id or self.env.company
            user_sudo = self.sudo().with_company(company.id)._create_user()

        if not user_sudo.active or not self.is_portal:
            user_sudo.write({'active': True, 'groups_id': [(4, group_portal.id), (3, group_public.id)]})
            user_sudo.partner_id.signup_prepare()

        self.with_context(active_test=True)._send_email()
