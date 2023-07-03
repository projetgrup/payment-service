# -*- coding: utf-8 -*-
import werkzeug

from odoo import http, _
from odoo.addons.payment_jetcheckout.controllers.main import PayloxController as Controller


class PayloxSaleController(Controller):

    @http.route('/payment/card/shop', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def shop(self, **kwargs):
        kwargs['result_url'] = '/shop/confirmation'
        url, tx, status = self._process(**kwargs)
        self._del()
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/order/<int:order>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def order(self, order, access_token, **kwargs):
        kwargs['result_url'] = '/my/orders/%s?access_token=%s' % (order, access_token)
        url, tx, status = self._process(**kwargs)
        self._del()
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/invoice/<int:invoice>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def invoice(self, invoice, access_token, **kwargs):
        kwargs['result_url'] = '/my/invoices/%s?access_token=%s' % (invoice, access_token)
        url, tx, status = self._process(**kwargs)
        self._del()
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/subscription/<int:subscription>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def subscription(self, subscription, access_token, **kwargs):
        kwargs['result_url'] = '/my/subscription/%s/%s' % (subscription, access_token)
        url, tx, status = self._process(**kwargs)
        self._del()
        return werkzeug.utils.redirect(url)
