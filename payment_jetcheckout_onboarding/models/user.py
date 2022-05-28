# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.addons.auth_signup.models.res_users import SignupError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def signup(self, values, token=None):
        self = self.sudo().with_context(onboarding=True)

        vals =  { key: values.get(key) for key in ('login', 'name', 'password') }
        db, login, password = super().signup(vals, token=token)
        user = self.env['res.users'].search([('login', '=', login)], limit=1)
        if not user:
            raise SignupError(_("Could not create a new account"))

        lang = values.get('lang', 'en_US')
        country_code = lang.split('_')[-1] if '_' in lang else lang # need improvement
        currency_code = 'USD' if country_code != 'TR' else 'TRY' # need improvement

        country = self.env['res.country'].search([('code','=',country_code)], limit=1)
        currency = self.env['res.currency'].search([('name','=',currency_code)], limit=1)
        company = self.env['res.company'].create({
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
        self.env['website'].create({
            'name': values['company'],
            'domain': values['domain'],
            'company_id': company.id,
        })
        user.write({
            'company_id': company.id,
            'company_ids': [(6, 0, company.ids)],
        })
        user.partner_id.write({
            'mobile': values['phone'],
        })
        return db, login, password
