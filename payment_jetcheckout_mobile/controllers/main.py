# -*- coding: utf-8 -*-
import uuid
import json
import base64
import logging
from Crypto.Cipher import AES

from odoo import fields, _
from odoo.http import request, route
from odoo.addons.payment_jetcheckout.controllers.main import PayloxController as Controller

_logger = logging.getLogger(__name__)


class PayloxController(Controller):

    def _get_encrypted_vals(self, tx):
        apikey = tx.acquirer_id.paylox_contactless_apikey.encode('utf-8')
        secretkey = tx.acquirer_id.paylox_contactless_secretkey.encode('utf-8')
        value = json.dumps({
            "amount": tx.amount,
            "callbackURL": "%s/payment/contactless/callback" % tx.jetcheckout_website_id.domain,
            "conversationId": tx.jetcheckout_order_id,
            #"paymentSource": "SOURCE",
        }).encode('utf-8')
        size = AES.block_size
        
        pad_len = size - len(value) % size
        padded = value + (bytes([pad_len]) * pad_len)
        cipher = AES.new(secretkey, AES.MODE_CBC, apikey)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')

    def _get_decrypted_vals(self, value):
        acquirer = self._get_acquirer()
        apikey = acquirer.paylox_contactless_apikey.encode('utf-8')
        secretkey = acquirer.paylox_contactless_secretkey.encode('utf-8')
        value = base64.b64decode(value.encode('utf-8'))
        cipher = AES.new(secretkey, AES.MODE_CBC, apikey)
        decrypted = cipher.decrypt(value).decode('utf-8')
        return decrypted[:-ord(decrypted[-1:])]

    def _get_tx_vals(self, **kwargs):
        res = super()._get_tx_vals(**kwargs)
        if kwargs.get('contactless'):
            res['paylox_contactless_ok'] = True
        return res

    def _process(self, **kwargs):
        url, tx, status = super()._process(**kwargs)
        if tx and kwargs.get('contactless'):
            tx.write({
                'state': 'done' if kwargs.get('status') else 'error',
                'state_message': kwargs.get('errorMessage'),
                'acquirer_reference': kwargs.get('paymentId'),
            })
        return url, tx, status

    @route('/payment/contactless/callback', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True, save_session=False)
    def callback_contactless(self, **kwargs):
        try:
            result = json.loads(self._get_decrypted_vals(kwargs['returnData']))
            result['contactless'] = True
            result['order_id'] = result['conversationId']
            url, tx, status = self._process(**result)
            if not status and tx.jetcheckout_order_id:
                url += '?=%s' % tx.jetcheckout_order_id
            return request.redirect(url)
        except Exception as e:
            _logger.error('An error occured when getting contactless payment: %s' % e)
            return request.redirect('/payment/card/result')

    @route(['/payment/card/pay'], type='json', auth='public', csrf=False, sitemap=False, website=True)
    def payment(self, **kwargs):
        if not kwargs.get('contactless'):
            return super().payment(**kwargs)

        self._check_user()

        amount = float(kwargs['amount'])
        rate = float(kwargs.get('discount', {}).get('single', 0))
        if rate > 0:
            amount = amount * (100 - rate) / 100

        acquirer = self._get_acquirer()
        currency = self._get_currency(kwargs['currency'], acquirer)
        partner = self._get_partner(kwargs['partner'], parent=True)

        order_id = str(uuid.uuid4())
        sale_id = int(kwargs.get('order', 0))
        invoice_id = int(kwargs.get('invoice', 0))

        tx = self._get_transaction()
        vals = {
            'acquirer_id': acquirer.id,
            'amount': amount,
            'operation': 'online_direct',
            'jetcheckout_website_id': request.website.id,
            'jetcheckout_ip_address': tx and tx.jetcheckout_ip_address or request.httprequest.remote_addr,
            'jetcheckout_url_address': tx and tx.jetcheckout_url_address or request.httprequest.referrer,
            'jetcheckout_order_id': order_id,
            'jetcheckout_payment_amount': amount,
            'jetcheckout_installment_count': 1,
            'jetcheckout_installment_amount': amount,
            'jetcheckout_installment_description': _('Single Payment'),
        }

        if tx:
            vals.update(self._get_tx_vals(**kwargs))
            tx.write(vals)
        else:
            vals.update({
                'amount': amount,
                'currency_id': currency.id,
                'acquirer_id': acquirer.id,
                'partner_id': partner.id,
                'operation': 'online_direct',
            })
            vals.update(self._get_tx_vals(**kwargs))
            tx = request.env['payment.transaction'].sudo().create(vals)

        if sale_id:
            tx.sale_order_ids = [(4, sale_id)]
        elif invoice_id:
            tx.invoice_ids = [(4, invoice_id)]

        self._set('tx', tx.id)

        encrypted = self._get_encrypted_vals(tx)
        if encrypted:
            return {'url': acquirer.paylox_contactless_url % encrypted, 'id': tx.id}
        else:
            tx.state = 'error'
            message = _('%s (Error Code: %s)') % (_('Error'), 0)
            tx.write({
                'state': 'error',
                'state_message': message,
                'last_state_change': fields.Datetime.now(),
            })
            values = {'error': message}
        return values
