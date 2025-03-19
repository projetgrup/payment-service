# -*- coding: utf-8 -*-
import json
import werkzeug.urls
import werkzeug.utils
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home


class OAuthLogin(Home):

    def list_providers(self):
        super().list_providers()
        try:
            auth_providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            auth_providers = []
        for rec in auth_providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = self.get_state(rec)
            params = dict(
                response_type=rec['response_type'],
                client_id=rec['client_id'],
                redirect_uri=return_url,
                scope=rec['scope'],
                state=json.dumps(state),
            )
            rec['auth_link'] = "%s?%s" % (rec['auth_endpoint'], werkzeug.urls.url_encode(params))
        return auth_providers
