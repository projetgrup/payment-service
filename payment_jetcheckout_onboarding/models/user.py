# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_users import SignupError

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def signup(self, values, token=None):
        vals =  { key: values.get(key) for key in ('login', 'name', 'password') }
        db, login, password = super().signup(vals, token=token)
        user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        if not user:
            raise SignupError(_("Could not create a new account."))

        country = self.env['res.country'].sudo().search([('code','=','TR')], limit=1)
        currency = self.env['res.currency'].sudo().search([('name','=','TRY')], limit=1)
        company = self.env['res.company'].sudo().create({
            'name': values['company'],
            'vat': values['vat'],
            'email': values['login'],
            'mobile': values['phone'],
            'country_id': country.id,
            'currency_id': currency.id,
            'website': values['domain'],
            'tax_office': values['tax'],
            'usage_type': values['type'],
        })

        user.write({
            'company_id': company.id,
            'company_ids': [(6, 0, company.ids)],
        })
        user.partner_id.write({
            'mobile': values['phone'],
        })

        website =  self.env['website'].sudo().create({
            'name': values['company'],
            'domain': values['domain'],
            'company_id': company.id,
        })
        return db, login, password
