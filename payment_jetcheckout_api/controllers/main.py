# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController

class JetcheckoutApiController(JetController):

    def _jetcheckout_get_transaction(self):
        return request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash','=',request.session.hash),('state','=','draft')], limit=1)

    def _jetcheckout_process(self, **kwargs):
        url, tx = super()._jetcheckout_process(**kwargs)
        if tx.jetcheckout_api_hash:
            if 'hash' in request.session:
                del request.session['hash']
            url = tx.jetcheckout_api_return_url
        return url, tx

    @http.route(['/payment'], type='http', methods=['GET', 'POST'], auth='public', csrf=False, sitemap=False, website=True)
    def jetcheckout_payment_api_page(self, **kwargs):
        hash = kwargs.get('hash') or request.session.get('hash')
        if not hash:
            raise AccessError(_('Access Denied'))

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '=', hash)], limit=1)
        if not tx:
            raise AccessError(_('Access Denied'))

        request.session['hash'] = hash
        acquirers = JetController._jetcheckout_get_acquirer()
        values = {
            'acquirers': acquirers,
            'tx': tx,
        }
        return request.render('payment_jetcheckout_api.payment_page', values)

    @http.route(['/payment/card'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def jetcheckout_payment_api_card_page(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '=', request.session['hash'])], limit=1)
        if not tx:
            raise AccessError(_('Access Denied'))

        values = self._jetcheckout_get_data(acquirer=tx.acquirer_id, company=tx.company_id, balance=False)
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.payment_card_page', values)

    @http.route(['/payment/bank'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def jetcheckout_payment_api_bank_page(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '=', request.session['hash'])], limit=1)
        if not tx:
            raise AccessError(_('Access Denied'))

        values = self._jetcheckout_get_data(acquirer=tx.acquirer_id, company=tx.company_id, balance=False)
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.payment_bank_page', values)

    @http.route(['/payment/bank/validate'], type='json', auth='public')
    def jetcheckout_payment_api_validate_page(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '=', request.session['hash'])], limit=1)
        if not tx:
            raise AccessError(_('Access Denied'))

        tx.write({'state': 'pending'})
        if 'hash' in request.session:
            del request.session['hash']
        return tx.jetcheckout_page_return_url
