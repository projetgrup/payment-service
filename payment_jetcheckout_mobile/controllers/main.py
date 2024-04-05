# -*- coding: utf-8 -*-
import re
import uuid
import json
import base64
import hashlib
import logging
import requests

from odoo import fields, _
from odoo.http import request, route
from odoo.tools.float_utils import float_compare, float_round
from odoo.addons.payment_jetcheckout.controllers.main import PayloxController as Controller

_logger = logging.getLogger(__name__)


class PayloxController(Controller):

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

    @route(['/payment/contactless/success', '/payment/contactless/fail'], type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True, save_session=False)
    def finalize_contactless(self, **kwargs):
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

        installment_count = 1
        campaign = kwargs.get('campaign', '')

        amount = float(kwargs['amount'])
        rate = float(kwargs.get('discount', {}).get('single', 0))
        if rate > 0 and installment == 1:
            amount = amount * (100 - rate) / 100
        amount_integer = round(amount * 100)
        amount_customer = 0

        acquirer = self._get_acquirer()
        currency = self._get_currency(kwargs['currency'], acquirer)
        partner = self._get_partner(kwargs['partner'], parent=True)

        order_id = str(uuid.uuid4())
        hash = base64.b64encode(hashlib.sha256(''.join([acquirer.jetcheckout_api_key, order_id, str(amount_integer), acquirer.jetcheckout_secret_key]).encode('utf-8')).digest()).decode('utf-8')
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_paylox_env(),
            "campaign_name": campaign,
            "amount": amount_integer,
            "currency": currency.name,
            "installment_count": installment_count,
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

        sale_id = int(kwargs.get('order', 0))
        invoice_id = int(kwargs.get('invoice', 0))

        tx = self._get_transaction()
        vals = {
            'acquirer_id': acquirer.id,
            'callback_hash': hash,
            'amount': amount,
            'fees': 0,
            'operation': 'online_direct',
            'jetcheckout_website_id': request.website.id,
            'jetcheckout_ip_address': tx and tx.jetcheckout_ip_address or request.httprequest.remote_addr,
            'jetcheckout_url_address': tx and tx.jetcheckout_url_address or request.httprequest.referrer,
            'jetcheckout_campaign_name': campaign,
            'jetcheckout_order_id': order_id,
            'jetcheckout_payment_amount': amount,
            'jetcheckout_installment_count': installment_count,
            'jetcheckout_installment_plus': 0,
            'jetcheckout_installment_description': False,
            'jetcheckout_installment_amount': amount,
            'jetcheckout_commission_rate': 0,
            'jetcheckout_commission_amount': 0,
            'jetcheckout_customer_rate': 0,
            'jetcheckout_customer_amount': 0,
        }

        if tx:
            vals.update(self._get_tx_vals(**kwargs))
            tx.write(vals)
        else:
            vals.update({
                'amount': amount,
                'fees': 0,
                'currency_id': currency.id,
                'acquirer_id': acquirer.id,
                'partner_id': partner.id,
                'operation': 'online_direct',
            })
            vals.update(self._get_tx_vals(**kwargs))
            tx = request.env['payment.transaction'].sudo().create(vals)

        if sale_id:
            tx.sale_order_ids = [(4, sale_id)]
            sale_order_id = request.env['sale.order'].sudo().browse(sale_id)
            billing_partner_id = sale_order_id.partner_invoice_id
            shipping_partner_id = sale_order_id.partner_shipping_id
            data.update({
                "billing_address": {
                    "contactName": billing_partner_id.name,
                    "address": "%s %s/%s/%s" % (billing_partner_id.street, billing_partner_id.city, billing_partner_id.state_id and billing_partner_id.state_id.name or '', billing_partner_id.country_id and billing_partner_id.country_id.name or ''),
                    "city": billing_partner_id.state_id and billing_partner_id.state_id.name or "",
                    "country": billing_partner_id.country_id and billing_partner_id.country_id.name or "",
                },
                "shipping_address": {
                    "contactName": shipping_partner_id.name,
                    "address": "%s %s/%s/%s" % (shipping_partner_id.street, shipping_partner_id.city, shipping_partner_id.state_id and shipping_partner_id.state_id.name or '', shipping_partner_id.country_id and shipping_partner_id.country_id.name or ''),
                    "city": shipping_partner_id.state_id and shipping_partner_id.state_id.name or "",
                    "country": shipping_partner_id.country_id and shipping_partner_id.country_id.name or "",
                },
            })

            if not float_compare(amount, sale_order_id.amount_total, 2):
                customer_basket = [{
                    "id": line.product_id.default_code or str(line.product_id.id),
                    "name": line.product_id.name,
                    "description": line.name,
                    "qty": line.product_uom_qty,
                    "amount": line.price_total,
                    "category": line.product_id.categ_id.name,
                    "is_physical": line.product_id.type == 'product',
                } for line in sale_order_id.order_line if line.price_total > 0]

                if amount_customer > 0:
                    product = request.env.ref('payment_jetcheckout.product_commission').sudo()
                    customer_basket.append({
                        "id": product.default_code or str(product.id),
                        "name": product.display_name,
                        "description": product.name,
                        "qty": 1.0,
                        "amount": round(float_round(amount_customer, 2), 2), # used double round, because format_round seems not working
                        "category": product.categ_id.name,
                        "is_physical": False,
                    })
                data.update({"customer_basket": customer_basket})

        elif invoice_id:
            tx.invoice_ids = [(4, invoice_id)]

        self._set('tx', tx.id)

        url = '%s/api/v1/payment/softpos' % acquirer._get_paylox_api_url()
        fullname = tx.partner_name.split(' ', 1)
        address = []
        if tx.partner_city:
            address.append(tx.partner_city)
        if tx.partner_state_id:
            address.append(tx.partner_state_id.name)
        if tx.partner_country_id:
            address.append(tx.partner_country_id.name)

        base_url = request.httprequest.host
        success_url = '/payment/contactless/success' if 'successurl' not in kwargs or not kwargs['successurl'] else kwargs['successurl']
        fail_url = '/payment/contactless/fail' if 'failurl' not in kwargs or not kwargs['failurl'] else kwargs['failurl']
        data.update({
            "order_id": order_id,
            "success_url": "https://%s%s" % (base_url, success_url),
            "fail_url": "https://%s%s" % (base_url, fail_url),
            "customer":  {
                "name": fullname[0],
                "surname": fullname[-1],
                "email": tx.partner_email,
                "id": str(tx.partner_id.id),
                "identity_number": tx.partner_id.vat,
                "phone": tx.partner_phone,
                "ip_address": tx.jetcheckout_ip_address or request.httprequest.remote_addr,
                "postal_code": tx.partner_zip,
                "company": tx.partner_id.parent_id and tx.partner_id.parent_id.name or "",
                "address": "%s %s" % (tx.partner_address, "/".join(address)),
                "city": tx.partner_state_id and tx.partner_state_id.name or "",
                "country": tx.partner_country_id and tx.partner_country_id.name or "",
            },
        })

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            txid = result['transaction_id']
            if result['response_code'] in ("00", "00307"):
                rurl = result['redirect_url']
                tx.write({
                    'state': 'pending',
                    'state_message': _('Transaction is pending...'),
                    'acquirer_reference': txid,
                    'jetcheckout_transaction_id': txid,
                    'last_state_change': fields.Datetime.now(),
                })
                return {'url': '%s/%s' % (rurl, txid), 'id': tx.id}
            else:
                tx.state = 'error'
                message = _('%s (Error Code: %s)') % (result['message'], result['response_code'])
                tx.write({
                    'state': 'error',
                    'state_message': message,
                    'acquirer_reference': txid,
                    'jetcheckout_transaction_id': txid,
                    'last_state_change': fields.Datetime.now(),
                })
                values = {'error': message}
        else:
            tx.state = 'error'
            message = _('%s (Error Code: %s)') % (response.reason, response.status_code)
            tx.write({
                'state': 'error',
                'state_message': message,
                'last_state_change': fields.Datetime.now(),
            })
            values = {'error': message}
        return values
