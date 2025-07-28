# -*- coding: utf-8 -*-

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.tools import file_open
from odoo.tools.translate import _
from odoo.http import request, content_disposition
from odoo.addons.web.controllers.main import Home as WebHome


class Home(WebHome):

    @http.route('/m/redirect', type='http', auth='none')
    def page_redirect(self, **kw):
        auth_token = request.httprequest.headers.get('Authorization-Token')
        if not auth_token:
            raise NotFound()

        route = request.env['web.mobile.route'].sudo().search([('token', '=', auth_token)], limit=1)
        return request.render('web_mobile_application.page_redirect', {
            'auth_token': auth_token,
            'route_urls': route.url_ids.mapped('url'),
        })

    @http.route('/m/redirect/save', type='json', auth='none')
    def page_redirect_save(self, url=None, token=None, **kw):
        if not url or not token:
            return False

        route = request.env['web.mobile.route'].sudo().search([('token', '=', token)], limit=1)
        if route and url not in route.url_ids.mapped('url'):
            route.url_ids = [(0, 0, {'url': url})]
        else:
            route.create({
                'token': token,
                'url_ids': [(0, 0, {'url': url})]
            })
        return True

    @http.route('/m/redirect/remove', type='json', auth='none')
    def page_redirect_remove(self, url=None, token=None, **kw):
        if not url or not token:
            return False

        route = request.env['web.mobile.route.url'].sudo().search([('route_id.token', '=', token), ('url', '=', url)], limit=1)
        route.unlink()
        return True

    @http.route('/m/apk', type='http', auth='none')
    def page_apk(self, **kw):
        name = 'jetcheckout'
        return request.make_response(
            file_open('web_mobile_application/static/apps/android/app.apk', 'rb').read(),
            [
                ('Content-Type', 'application/vnd.android.package-archive'),
                ('Content-Disposition', content_disposition('%s.apk' % name)),
                ('Cache-Control', 'no-store'),
            ]
        )

    @http.route('/.well-known/assetlinks.json', type='http', auth='none')
    def page_assetlinks(self, **kw):
        return request.make_response(
            file_open('web_mobile_application/static/apps/android/assetlinks.json', 'r').read(),
            [
                ('Content-Type', 'application/json'),
                ('Content-Disposition', content_disposition('assetlinks.json')),
                ('Cache-Control', 'no-store'),
            ]
        )
