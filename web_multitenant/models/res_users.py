# -*- coding: utf-8 -*-
import inspect
from odoo import api, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    _sql_constraints = [
        ('login_key', 'unique (login, company_id)', 'You can not have two users with the same login!'),
    ]

    @api.constrains('login', 'company_id')
    def _check_login(self):
        self.flush(['login', 'company_id'])
        self.env.cr.execute(
            """
                SELECT login, company_id, COUNT(*)
                FROM res_users
                WHERE login IN (SELECT login FROM res_users WHERE id IN %s)
                GROUP BY login, company_id
                HAVING count(*) > 1 LIMIT 100
            """,
            (tuple(self.ids),)
        )
        if self.env.cr.rowcount:
            raise ValidationError(_('You can not have two users with the same login!'))

    @api.model
    def _get_login_domain(self, login):
        #domain = super(ResUsers, self)._get_login_domain(login)
        domain = [('login', '=', login)]
        website = self.env['website'].get_current_website()
        if website:
            websites = self.env['website'].sudo().search([('domain', '=', website.domain)])

            frame = inspect.currentframe().f_back
            args = frame.f_locals
            env = args.get('user_agent_env')
            companies = [env['company']] if 'company' in env else websites.mapped('company_id').ids
            domain += ['|', ('share', '=', False), '&', '&', ('share', '=', True), ('website_id', 'in', tuple([False] + websites.ids)), ('company_id', 'in', companies)]
        return domain

    @api.model
    def _get_email_domain(self, email):
        #domain = super(ResUsers, self)._get_email_domain(login)
        domain = [('email', '=', email)]
        website = self.env['website'].get_current_website()
        if website:
            websites = self.env['website'].sudo().search([('domain', '=', website.domain)])
            companies = websites.mapped('company_id')
            domain.extend([('company_id', 'in', companies.ids), ('website_id', 'in', tuple([False] + websites.ids))])
        return domain
