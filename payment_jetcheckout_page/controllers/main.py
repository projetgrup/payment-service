# -*- coding: utf-8 -*-
import werkzeug
import logging
import urllib.parse

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.base_rest.controllers import main
from odoo.addons.payment_jetcheckout.controllers.main import jetcheckoutController as jetController

_logger = logging.getLogger(__name__)

class PaymentAPIController(main.RestController):
    _root_path = "/page/"
    _collection_name = "payment.api.services"
    _default_auth = "public"

class jetcheckoutPageController(jetController):

    def jetcheckout_process(self, **kwargs):
        if 'order_id' not in kwargs:
            return werkzeug.utils.redirect('/404')

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id','=',kwargs.get('order_id'))], limit=1)
        if not tx:
            return werkzeug.utils.redirect('/404')

        if int(kwargs.get('response_code')) == 0:
            tx.write({'state': 'done'})
            if hasattr(tx, 'sale_order_ids') and tx.sale_order_ids:
                tx.jetcheckout_validate_order()
            tx.jetcheckout_payment()
        else:
            tx.write({
                'state': 'error',
                'state_message': _('%s (Error Code: %s)') % (kwargs.get('message', '-'), kwargs.get('response_code','')),
            })
        if 'hash' in request.session:
            del request.session['hash']
        return werkzeug.utils.redirect('%s?=%s' % (tx.jetcheckout_page_return_url, urllib.parse.quote_plus(tx.jetcheckout_page_hash)))

    @http.route(['/payment/redirect'], type='http', methods=['GET'], auth='none', csrf=False, sitemap=False, website=True)
    def jetcheckout_full_redirect_page(self, **kwargs):
        request.session.hash = urllib.parse.unquote(kwargs[''])
        return werkzeug.utils.redirect('/payment')

    @http.route(['/payment'], type='http', methods=['GET'], auth='none', csrf=False, sitemap=False, website=True)
    def jetcheckout_full_payment_page(self, **kwargs):
        request.session.uid = False
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_page_hash','=',request.session.hash)], limit=1)
        if not tx:
            raise ValidationError(_('Access Denied'))
        acquirers = jetController.jetcheckout_get_acquirer(jetController)
        values = {
            'acquirers': acquirers,
            'tx': tx,
            }
        return request.render('payment_jetcheckout_page.payment_page', values)

    @http.route(['/payment/card'], type='http', methods=['GET'], auth='none', csrf=False, sitemap=False, website=True)
    def jetcheckout_full_payment_card_page(self, **kwargs):
        request.session.uid = False
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_page_hash','=',request.session.hash)], limit=1)
        if not tx:
            raise ValidationError(_('Access Denied'))
        values = self.jetcheckout_get_data(acquirer=tx.acquirer_id, company=tx.company_id, balance=False)
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_page.payment_card_page', values)

    @http.route(['/payment/bank'], type='http', methods=['GET'], auth='none', csrf=False, sitemap=False, website=True)
    def jetcheckout_full_payment_bank_page(self, **kwargs):
        request.session.uid = False
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_page_hash','=',request.session.hash)], limit=1)
        if not tx:
            raise ValidationError(_('Access Denied'))
        values = self.jetcheckout_get_data(acquirer=tx.acquirer_id, company=tx.company_id, balance=False)
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_page.payment_bank_page', values)

    @http.route(['/payment/bank/validate'], type='json', auth='none')
    def jetcheckout_full_bank_validate_page(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_page_hash','=',request.session.hash)], limit=1)
        if not tx:
            raise ValidationError(_('Access Denied'))

        tx.write({'state': 'pending'})
        if 'hash' in request.session:
            del request.session['hash']
        return '%s?=%s' % (tx.jetcheckout_page_return_url, urllib.parse.quote_plus(tx.jetcheckout_page_hash))
