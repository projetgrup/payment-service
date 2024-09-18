# -*- coding: utf-8 -*-
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
        return super(ResUsers, self)._get_login_domain(login) + [('company_id', '=', self.env.company.id)]

    @api.model
    def _get_email_domain(self, email):
        return super()._get_email_domain(email) + [('company_id', '=', self.env.company.id)]

    @api.model
    def _get_login_order(self):
        return 'company_id, ' + super(ResUsers, self)._get_login_order()

    def write(self, values):
        if 'password' in values:
            for user in self:
                if user.has_group('base.group_user'):
                    users = self.search([('id', '!=', user.id), ('login', '=', user.login)]).filtered(lambda u: u.has_group('base.group_user'))
                    super(ResUsers, users).write({'password': values['password']})

        return super(ResUsers, self).write(values)
