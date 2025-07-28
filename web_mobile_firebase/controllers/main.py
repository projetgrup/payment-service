# -*- coding: utf-8 -*-
import re
from odoo.http import request
from odoo.addons.web.controllers.main import Home as WebHome


class Home(WebHome):

    def _save_firebase_token(self, token):
        user = request.env.user.sudo()
        agent = request.httprequest.headers.get('User-Agent')
        if token and user and not user.firebase_token_ids.filtered(lambda t: t.token == token):
            match = re.search(r'\((.*?)\)', agent)
            user.firebase_token_ids = [(0, 0, {
                'token': token,
                'name': match.group(1) if match else ''
            })]

    def web_client(self, s_action=None, **kw):
        res = super(Home, self).web_client(s_action=s_action, **kw)
        if 'firebase_token' in kw:
            if res.headers.get('Location'):
                request.session['firebase_token'] = kw['firebase_token']
            else:
                self._save_firebase_token(kw['firebase_token'])
        elif 'firebase_token' in request.session:
            self._save_firebase_token(request.session['firebase_token'])
            del request.session['firebase_token']
        return res
