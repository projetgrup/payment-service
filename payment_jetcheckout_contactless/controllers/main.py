# -*- coding: utf-8 -*-
import re
import uuid
import json
import base64
import hashlib
from Crypto.Cipher import AES

from odoo import fields, _
from odoo.http import request, route
from odoo.tools.float_utils import float_round
from odoo.addons.payment_jetcheckout.controllers.main import PayloxController as Controller


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

    def _get_tx_vals(self, **kwargs):
        res = super()._get_tx_vals(**kwargs)
        if kwargs.get('contactless'):
            res['paylox_contactless_ok'] = True
        return res

    @route('/payment/contactless/callback', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def callback_contactless(self, **kwargs):
        raise Exception(kwargs)

    @route(['/payment/card/pay'], type='json', auth='public', csrf=False, sitemap=False, website=True)
    def payment(self, **kwargs):
        if not kwargs.get('contactless'):
            return super().payment(**kwargs)

        self._check_user()

        rows = kwargs['installment']['rows']
        installment = kwargs['installment']['id']
        campaign = kwargs.get('campaign', '')

        amount = float(kwargs['amount'])
        rate = float(kwargs.get('discount', {}).get('single', 0))
        if rate > 0 and installment == 1:
            amount = amount * (100 - rate) / 100

        type = self._get_type()
        if type == 'c':
            index = kwargs['installment']['index']
            installment = next(filter(lambda x: x['id'] == installment, rows), None)
            installment = next(filter(lambda x: x['index'] == index, installment['ids']), None)
        elif type == 'ct':
            index = kwargs['installment']['id']
            installment = next(filter(lambda x: x['id'] == index and x['campaign'] == campaign, rows), None)
        else:
            installment = next(filter(lambda x: x['id'] == installment, rows), None)

        amount_customer = amount * installment['crate'] / 100
        amount_total = float_round(amount + amount_customer, 2)
        amount_cost = float_round(amount_total * installment['corate'] / 100, 2)
        amount_integer = round(amount_total * 100)

        acquirer = self._get_acquirer()
        currency = self._get_currency(kwargs['currency'], acquirer)
        partner = self._get_partner(kwargs['partner'], parent=True)
        year = str(fields.Date.today().year)[:2]
        hash = base64.b64encode(hashlib.sha256(''.join([acquirer.jetcheckout_api_key, str(kwargs['card']['number']), str(amount_integer), acquirer.jetcheckout_secret_key]).encode('utf-8')).digest()).decode('utf-8')
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_paylox_env(),
            "campaign_name": campaign,
            "amount": amount_integer,
            "currency": currency.name,
            "installment_count": installment['count'],
            "card_number": kwargs['card']['number'],
            "expire_month": kwargs['card']['date'][:2],
            "expire_year": year + kwargs['card']['date'][-2:],
            "is_3d": True,
            "hash_data": hash,
            "language": "tr",
        }

        if getattr(partner, 'tax_office_id', False):
            data.update({'billing_tax_office': partner.tax_office_id.name})
        elif getattr(partner, 'tax_office', False):
            data.update({'billing_tax_office': partner.tax_office})

        if partner.vat:
            partner_vat = re.sub(r'[^\d]', '', partner.vat)
            if partner_vat and len(partner_vat) in (10, 11):
                data.update({'billing_tax_number': partner_vat})

        order_id = str(uuid.uuid4())
        sale_id = int(kwargs.get('order', 0))
        invoice_id = int(kwargs.get('invoice', 0))

        tx = self._get_transaction()
        vals = {
            'acquirer_id': acquirer.id,
            'callback_hash': hash,
            'amount': amount_total,
            'fees': amount_cost,
            'operation': 'online_direct',
            'jetcheckout_website_id': request.website.id,
            'jetcheckout_ip_address': tx and tx.jetcheckout_ip_address or request.httprequest.remote_addr,
            'jetcheckout_url_address': tx and tx.jetcheckout_url_address or request.httprequest.referrer,
            'jetcheckout_campaign_name': campaign,
            'jetcheckout_card_name': kwargs['card']['holder'],
            'jetcheckout_card_number': ''.join([kwargs['card']['number'][:6], '*'*6, kwargs['card']['number'][-4:]]),
            'jetcheckout_card_type': kwargs['card']['type'].capitalize(),
            'jetcheckout_card_family': kwargs['card']['family'].capitalize(),
            'jetcheckout_order_id': order_id,
            'jetcheckout_payment_amount': amount,
            'jetcheckout_installment_count': installment['count'],
            'jetcheckout_installment_plus': installment['plus'],
            'jetcheckout_installment_description': installment['idesc'],
            'jetcheckout_installment_amount': amount / installment['count'] if installment['count'] > 0 else amount,
            'jetcheckout_commission_rate': installment['corate'],
            'jetcheckout_commission_amount': amount_cost,
            'jetcheckout_customer_rate': installment['crate'],
            'jetcheckout_customer_amount': amount_customer,
        }

        if tx:
            vals.update(self._get_tx_vals(**kwargs))
            tx.write(vals)
        else:
            vals.update({
                'amount': amount_total,
                'fees': amount_cost,
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