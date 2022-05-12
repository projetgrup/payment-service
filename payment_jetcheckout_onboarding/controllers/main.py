# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError

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

        try:
            field_check = self._check_signup_values(qcontext)
            if 'error' in field_check:
                return field_check
            domain = qcontext['domain']
            self.do_signup(qcontext)
            if qcontext.get('token'):
                User = request.env['res.users']
                user_sudo = User.sudo().search(User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1)
                template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)
            return {'redirect_url': 'http://' + domain + '/web'}
        except UserError as e:
            return {
                'error': e.args[0],
            }
        except (SignupError, AssertionError) as e:
            if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                return {
                    'error':  _("Another user is already registered using this email address."),
                    'element': 'login',
                    'page': 0
                }
            else:
                _logger.error("%s", e)
                return {
                    'error':  _("Could not create a new account."),
                }

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
        if request.env['res.company'].sudo().search_count([('vat','=',vals['vat'])]):
            return {
                'error': _("There is already a registered company with same VAT number, please check it."),
                'element': 'vat',
                'page': 1
            }
        return {}

    def _prepare_signup_values(self, values):
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        return values
