# -*- coding: utf-8 -*-

import base64

from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller
from odoo.addons.sec_audit.controllers.main import AuditController


class PayloxAuditController(AuditController):
    
    def _auth(self):
        headers = request.httprequest.headers
        if 'Authorization' not in headers:
            raise AccessError('No Authorization header set')

        code = headers.get('Authorization').split(' ', 1)[1]
        auth = base64.b64decode(code).decode('utf-8')
        username, password = auth.split(':', 1)
        token = request.env['payment.acquirer.jetcheckout.api'].sudo().search([
            ('api_key', '=', username),
            ('secret_key', '=', password)
        ], limit=1)
        if not token:
            raise AccessError('Wrong username or password')
        if not token.perm_audit:
            raise AccessError('This token is not allowed to use audit services')
        if not token.company_id.sec_audit_webservice_ok:
            raise AccessError('Audit service is not active for this company')
        return token


class PayloxSystemApiController(Controller):

    def _get_template(self, path, values):
        if 'tx' in values and values['tx'] and values['tx']['jetcheckout_api_ok']:
            template = request.env['payment.view'].sudo().search([
                ('page_id.path', '=', path),
                '|',
                ('company_id', '=', values['company']['id'] or 0),
                ('company_id', '=', values['company']['parent_id']['id'] or 0),
            ], order='id desc', limit=1)
            if template:
                values.update({
                    'template': {
                        'id': template.uid,
                        'js': bool(template.arch_js),
                        'css': bool(template.arch_css),
                    }
                })
                return template.view_id.id
            if path.startswith('/payment'):
                if path.startswith('/payment/card'):
                    return 'payment_jetcheckout_api.page_card'
                return 'payment_jetcheckout_api.payment_page'
        return super()._get_template(path, values)
