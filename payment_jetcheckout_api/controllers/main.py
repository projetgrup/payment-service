# -*- coding: utf-8 -*-
import werkzeug
import requests

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


class JetcheckoutApiController(JetController):

    def _confirm_bank_webhook(self, tx):
        try:
            url = tx.jetcheckout_api_bank_webhook_url
            data = {'id': tx.jetcheckout_api_id}
            response = requests.post(url, data=data)
            if response.status_code == 200:
                tx.write({'state': 'pending'})
            else:
                raise ValidationError('%s (Error Code: %s)' % (response.reason, response.status_code))
        except Exception as e:
            raise ValidationError(e)
        except:
            raise ValidationError('%s (Error Code: %s)' % ('Server Error', '-1'))

    def _jetcheckout_get_transaction(self):
        hash = request.session.get('hash')
        if not hash:
            return False
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '=', hash), ('state', '=', 'draft')], limit=1)
        if not tx:
            raise ValidationError(_('An error occured. Please restart your payment transaction.'))
        return tx

    def _jetcheckout_process(self, **kwargs):
        url, tx = super()._jetcheckout_process(**kwargs)
        if tx.jetcheckout_api_hash:
            if 'hash' in request.session:
                del request.session['hash']
            url = tx.jetcheckout_api_card_return_url
        return url, tx

    @http.route(['/payment'], type='http', methods=['GET', 'POST'], auth='public', csrf=False, sitemap=False, website=True)
    def jetcheckout_payment_api_page(self, **kwargs):
        hash = kwargs.get('hash') or request.session.get('hash')
        if not hash:
            raise werkzeug.exceptions.NotFound()

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '=', hash),('state', '=', 'draft')], limit=1)
        if not tx:
            raise werkzeug.exceptions.NotFound()

        request.session['hash'] = hash
        acquirers = JetController._jetcheckout_get_acquirer()
        order = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '!=', hash),('state', '=', 'pending'), ('jetcheckout_api_order', '=', tx.jetcheckout_api_order)], limit=1)
        values = {
            'acquirers': acquirers,
            'tx': tx,
            'order': order
        }
        return request.render('payment_jetcheckout_api.payment_page', values, headers={'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'})

    @http.route(['/payment/card'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def jetcheckout_payment_api_card_page(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '=', request.session.get('hash')),('state','=','draft')], limit=1)
        if not tx:
            raise werkzeug.exceptions.NotFound()

        values = self._jetcheckout_get_data(acquirer=tx.acquirer_id, company=tx.company_id, balance=False)
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.payment_card_page', values, headers={'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'})

    @http.route(['/payment/bank'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def jetcheckout_payment_api_bank_page(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '=', request.session.get('hash')), ('state', '=', 'draft')], limit=1)
        if not tx:
            raise werkzeug.exceptions.NotFound()

        order = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '!=', request.session.get('hash')),('state', '=', 'pending'), ('jetcheckout_api_order', '=', tx.jetcheckout_api_order)], limit=1)
        if order:
            self._confirm_bank_webhook(tx)
            return werkzeug.utils.redirect('/payment/bank/result')

        values = self._jetcheckout_get_data(acquirer=tx.acquirer_id, company=tx.company_id, balance=False)
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.payment_bank_page', values, headers={'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'})

    @http.route(['/payment/bank/result'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def jetcheckout_payment_api_bank_success_page(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '=', request.session.get('hash')), ('state', '=', 'pending')], limit=1)
        if not tx:
            raise werkzeug.exceptions.NotFound()

        values = self._jetcheckout_get_data(acquirer=tx.acquirer_id, company=tx.company_id, balance=False)
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.payment_bank_page', values, headers={'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'})

    @http.route(['/payment/bank/confirm'], type='json', auth='public')
    def jetcheckout_payment_api_bank_validate(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '=', request.session.get('hash')), ('state', '=', 'draft')], limit=1)
        if not tx:
            return '/404'

        self._confirm_bank_webhook(tx)
        return '/payment/bank/result'

    @http.route(['/payment/bank/return'], type='json', auth='public')
    def jetcheckout_payment_api_return(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '!=', False),('jetcheckout_api_hash', '=', request.session.get('hash'))], limit=1)
        if not tx:
            return '/404'

        if 'hash' in request.session:
            del request.session['hash']

        return tx.jetcheckout_api_bank_return_url
