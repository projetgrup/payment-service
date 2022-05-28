# -*- coding: utf-8 -*-
import werkzeug

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

import socket
import logging
_logger = logging.getLogger(__name__)

SIGN_UP_REQUEST_PARAMS = {'phone', 'company', 'vat', 'tax', 'domain', 'type'}

class AuthSignupHome(AuthSignupHome):

    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        ncontext = {k: v for (k, v) in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        return {**qcontext, **ncontext}

    @http.route(['/web/signup/prepare'], type='json', auth='public', sitemap=False, website=True)
    def web_auth_signup_prepare(self, **qcontext):
        qcontext.update(self.get_auth_signup_config())
        if not qcontext.get('token') and request.session.get('auth_signup_token'):
            qcontext['token'] = request.session.get('auth_signup_token')
        if qcontext.get('token'):
            try:
                token_infos = request.env['res.partner'].sudo().signup_retrieve_info(qcontext.get('token'))
                for k, v in token_infos.items():
                    qcontext.setdefault(k, v)
            except:
                qcontext['error'] = _("Invalid signup token")
                qcontext['invalid_token'] = True

        if qcontext.get('error'):
            return qcontext

        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        create_date = datetime.now() - relativedelta(seconds=1)
        try:
            field_check = self._check_signup_values(qcontext)
            if 'error' in field_check:
                return field_check

            domain = qcontext['domain']
            self.do_signup(qcontext)
            self._create_nginx_config(domain)
            return {'redirect_url': 'http://%s/web/login/%s/%s/%s' % (domain, request.session.db, qcontext['login'], qcontext['password'])}

        except Exception as e:
            users = request.env['res.users'].sudo().search([('login', '=', qcontext['login']), ('active', 'in', [True,False]), ('create_date', '>', create_date)])
            if users:
                partners = users.mapped('partner_id')
                users.unlink()
                partners.unlink()

            company = request.env['res.company'].sudo().search([('name', '=', qcontext['company']), ('create_date', '>', create_date)])
            if company:
                website = request.env['website'].sudo().search([('company_id', '=', company.id), ('create_date', '>', create_date)])
                website.unlink()
                users = request.env['res.users'].sudo().search([('company_id', '=', company.id), ('active', 'in', [True,False]), ('create_date', '>', create_date)])
                if users:
                    partners = users.mapped('partner_id')
                    users.unlink()
                    partners.unlink()

                users = request.env['res.users'].sudo().search([('company_ids', 'child_of', [company.id]), ('active', 'in', [True,False]), ('create_date', '>', create_date)])
                users.write({'company_ids': [(3, company.id)]})

                property = request.env['ir.property'].sudo().search([('company_id', '=', company.id), ('create_date', '>', create_date)])
                property.unlink()

                partner = company.partner_id
                company.unlink()
                partner.unlink()

            message = _("Could not create a new account (%s)") % e
            return {'error':  message}

    @http.route(['/web/signup/domain'], type='json', auth='public', sitemap=False, website=True)
    def web_auth_signup_domain(self, **vals):
        try:
            base = socket.gethostbyname(request.httprequest.host)
            host = socket.gethostbyname(vals.get('domain'))
            if not base == host:
                return {
                    'error': _("Your domain points to %s, but its A record has to point to %s for proper usage. You can set this after signup.") % (host, base)
                }
            else:
                return {
                    'success': _("Your domain seems to be set correctly, it points to %s.") % (base,)
                }
        except:
            return {
                'error': _("This domain could not be resolved. Please enter a valid domain.")
            }

    def _check_signup_values(self, vals):
        if vals['password'] != vals['confirm_password']:
            return {
                'error': _("Passwords do not match; please retype them."),
                'element': 'password',
                'page': 0
            }
        elif request.env['res.users'].sudo().search_count([('login','=',vals['login'])]):
            return {
                'error': _("There is already a registered user with same email, please choose another one."),
                'element': 'login',
                'page': 0
            }
        elif request.env['res.company'].sudo().search_count([('vat','=',vals['vat'])]):
            return {
                'error': _("There is already a registered company with same VAT number, please check it."),
                'element': 'vat',
                'page': 1
            }
        elif request.env['res.company'].sudo().search_count([('name','=',vals['company'])]):
            return {
                'error': _("There is already a registered company with same name, please choose another one."),
                'element': 'company',
                'page': 1
            }
        elif request.env['website'].sudo().search_count([('domain','ilike',vals['domain'])]):
            return {
                'error': _("There is already a registered domain with same name, please choose another one."),
                'element': 'domain',
                'page': 2
            }
        return {}

    def _prepare_signup_values(self, values):
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        return values

    def _create_nginx_config(self, domain):
        try:
            if request.env['ir.module.module'].sudo().search_count([('name','=','website_custom_domain')]):
                config = request.env['nginx.domain.config'].sudo().create({'domain': domain})
                config.save()
        except:
            return

    def _signup_with_values(self, token, values):
        request.env['res.users'].sudo().signup(values, token)

    @http.route(['/web/login/<database>/<login>/<password>'], type='http', auth='public', sitemap=False, website=True)
    def web_auth_login(self, database, login, password, **kwargs):
        uid = request.session.authenticate(database, login, password)
        if not uid:
            return request.redirect('/web/login#test')
        return request.redirect('/web')
