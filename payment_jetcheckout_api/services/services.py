# -*- coding: utf-8 -*-
import json
import uuid
import time
import base64
import hashlib
import logging
import requests
import datetime
import functools
from urllib.parse import quote

from odoo import fields
from odoo.http import Response, request
from odoo.exceptions import AccessError
from odoo.tools.translate import _, _lt
from odoo.tools.float_utils import float_round
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.components.service import skip_secure_response
from odoo.addons.base_rest.controllers.main import RestController
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

TIMEOUT = 30
RESPONSE = {
    200: {"status": 0, "message": "Success"}
}

def auth(env):
    headers = request.httprequest.headers
    if 'Authorization' not in headers:
        raise AccessError('No Authorization header set')

    code = headers.get('Authorization').split(' ', 1)[1]
    auth = base64.b64decode(code).decode('utf-8')
    username, password = auth.split(':', 1)
    token = env['payment.acquirer.jetcheckout.api'].sudo().search([
        ('api_key', '=', username),
        ('secret_key', '=', password)
    ], limit=1)
    if not token:
        raise AccessError('Wrong username or password')
    return token


class PaymentAPIController(RestController):
    _root_path = "/api/v1/"
    _collection_name = "payment"
    _default_auth = "public"


class PaymentAPIService(Component):
    _inherit = "base.rest.service"
    _name = "payment"
    _usage = "payment"
    _collection = "payment"
    _description = _lt("""
        <br/>
        <h1 class="dCEJze">Description</h1>
        <p>This API helps you create payments and query their statuses with a special key which is privately generated for you.</p>
        <p>Firstly, use "Prepare Payment" method to initialize a payment request. Then, if everything goes well, server will send you a hash string.</p>
        <p>Now, you can navigate to <code>/payment/card?=&lt;hash&gt;</code> address to get payment form.</p>
        <p>When payment is done, its result will send to the address which you have specified when initializing the payment.</p>
        <p>Afterwards, you can use "Payment Operation" methods for cancelling, refunding, expiring or deleting the payment.</p>
    """)

    @restapi.method(
        [(["/installments"], "GET")],
        input_param=Datamodel("payment.installment.input"),
        output_param=Datamodel("payment.installment.output"),
        auth="public",
        tags=[_lt("Payment Initialization")]
    )
    def payment_installments(self, params):
        try:
            log = None
            loggable = self._log_state()
            if loggable:
                log = {
                    'service': 'api_get_installment',
                    'now': time.time(),
                    'method': 'get',
                    'url': '/payment/installments',
                    'request': json.dumps(params.dump(), indent=4, default=str, ensure_ascii=False),
                }
        except:
            log = None
            loggable = None

        try:
            api = self._get_api(params.apikey)
            if not api:
                status, message = 401, _('Application key does not match.')
                if loggable:
                    log.update({
                        'code': status,
                        'status': False,
                        'message': message,
                        'response': message,
                    })
                    self._log(log)
                return Response(message, status=status, mimetype="application/json")

            if loggable:
                log.update({
                    'partner': api.company_id.partner_id.id,
                    'company': api.company_id.id,
                })

            installments = self._get_installments(api, params, log=log)
            response = dict(**installments, **RESPONSE[200])

            if loggable:
                log.update({
                    'code': 200,
                    'status': True,
                    'message': _('Success'),
                    'response': json.dumps(response, indent=4, default=str, ensure_ascii=False),
                })
                self._log(log)

            ResponseOk = self.env.datamodels["payment.installment.output"]
            return ResponseOk(**response)

        except Exception as e:
            status, message = 500, _('An error occured')
            if loggable:
                log.update({
                    'code': status,
                    'status': False,
                    'message': message,
                    'response': str(e),
                })
                self._log(log)

            _logger.error(e)
            return Response('%s.\n%s' % (message, e), status=status, mimetype="application/json")

    payment_installments.__doc__ = _lt("Get Installments")

    @restapi.method(
        [(["/prepare"], "POST")],
        input_param=Datamodel("payment.prepare.input"),
        output_param=Datamodel("payment.prepare.output"),
        auth="public",
        tags=[_lt("Payment Initialization")]
    )
    def payment_prepare(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            tx = self._create_transaction(api, hash, params)

            ResponseOk = self.env.datamodels["payment.prepare.output"]
            if tx.jetcheckout_payment_type == 'physicalpos' and getattr(params, 'payNow', False):
                method = fields.first(tx.paylox_api_method_ids.filtered(lambda m: m.type == 'physicalpos'))
                status, message = 0, 'Success'
                acquirer = tx.acquirer_id
                url = acquirer._get_paylox_api_url()
                apikey = acquirer.jetcheckout_api_key
                base_url = acquirer.get_base_url()
                if base_url.endswith('/'):
                    base_url = base_url[:-1]
                payload = {
                    'application_key': apikey,
                    'order_id': tx.jetcheckout_order_id,
                    'amount': int(tx.amount*100),
                    'currency': tx.company_id.currency_id.name,
                    'store_code': tx.company_id.payment_method_physical_pos_store_code or '',
                    'callback_api_url': '%s/payment/callback' % base_url,
                    'mode': acquirer._get_paylox_env(),
                    #'document_type': 4,
                }
                if tx.paylox_product_ids:
                    precision = self.env['decimal.precision'].sudo().precision_get('Product Price')
                    payload.update({
                        'sale_items': [{
                            'name': product.name or '',
                            'barcode': product.code or '',
                            'qty': round(product.qty, precision),
                            'price': round(product.price, precision),
                            'amount': round(product.qty*product.price, precision),
                            'tax_rate': 20
                        } for product in tx.paylox_product_ids]
                    })

                devices = method.type_physicalpos_ids
                device_ids = []
                device_owner = ''
                device_name = ''
                if devices:        
                    device_owner = devices[0].type
                    if device_owner == 'pavo':
                        device_name = devices[0].name
                        device_ids.append(device_name)
                    else:
                        device_name = devices[0].name
                        device_ids.extend(devices.mapped('name'))

                if device_ids:
                    payload.update({'device_ids': device_ids})

                if device_owner:
                    payload.update({'device_owner': device_owner})

                request_count = 0
                status = 0
                message = ''
                def init_physical_payment():
                    nonlocal request_count
                    nonlocal status
                    nonlocal message
                    if request_count == 5:
                        status, message = 1, _('Request cycle exceeded. Please contact with system administrator.')
                        tx.write({
                            'state': 'error',
                            'state_message': message,
                            'last_state_change': fields.Datetime.now(),
                        })

                    request_count += 1
                    response = requests.post('%s/api/v1/physical/payment' % url, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        if result['response_code'] == '00158':
                            response = requests.post('%s/api/v1/physical/pairing' % url, json={
                                "application_key": apikey,
                                "device_id": device_name,
                                "device_owner": device_owner
                            })
                            if response.status_code == 200:
                                result = response.json()
                                if result['pairing_code']:
                                    status, message = 0, _('Pairing code is %s') % result['pairing_code']
                                else:
                                    status, message = 1, _('%s - (Error Code: %s)') % (result['message'], result['response_code'])
                                    tx.write({
                                        'state': 'error',
                                        'state_message': message,
                                        'last_state_change': fields.Datetime.now(),
                                    })
                            else:
                                status, message = 1, _('%s - (Error Code: %s)') % (response.reason, response.status_code)
                                tx.write({
                                    'state': 'error',
                                    'state_message': message,
                                    'last_state_change': fields.Datetime.now(),
                                })

                        elif result['response_code'] == '00202':
                            tx.write({
                                'state': 'pending', 
                                'last_state_change': fields.Datetime.now(),
                                'jetcheckout_payment_type': 'physicalpos',
                                'jetcheckout_transaction_id': result['transaction_id'],
                                'jetcheckout_payment_type_physicalpos_request_id': result['pos_order_number'],
                                'jetcheckout_payment_type_physicalpos_serial_id': device_name,
                            })
                            status, message = 0, _('Payment #%s is ready. Please check the PoS device.') % result['pos_order_number']

                        elif result['response_code'] == '00122':
                            order_aux_id = 'x%s' % str(uuid.uuid4())
                            tx.write({'jetcheckout_order_aux_id': order_aux_id})
                            payload.update({"order_id": order_aux_id})
                            init_physical_payment()

                        else:
                            status, message = 1, _('%s - (Error Code: %s)') % (result['message'], result['response_code'])
                            tx.write({
                                'state': 'error',
                                'state_message': message,
                                'last_state_change': fields.Datetime.now(),
                            })

                    else:
                        status, message = 1, _('%s - (Error Code: %s)') % (response.reason, response.status_code)
                        tx.write({
                            'state': 'error',
                            'state_message': message,
                            'last_state_change': fields.Datetime.now(),
                        })

                init_physical_payment()
                http_status = 400 if status else 200
                return Response(json.dumps(dict(status=status, message=message)), status=http_status, mimetype="application/json")

            hash = quote(hash)
            url = 'https://%s/payment?=%s' % (request.httprequest.host, hash)
            return ResponseOk(hash=hash, url=url, **RESPONSE[200])
        except Exception as e:
            _logger.error(e, exc_info=True)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_prepare.__doc__ = _lt("Prepare Payment")

    @skip_secure_response
    @restapi.method(
        [(["/init"], "POST")],
        input_param=Datamodel("payment.init.input"),
        output_param=Datamodel("payment.init.output"),
        auth="public",
        tags=[_lt("Payment Initialization")]
    )
    def payment_init(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            response = self._initialize_transaction(api, hash, params)
            if isinstance(response, Response):
                return response

            return Response(json.dumps({**RESPONSE[200], **response}), status=200, mimetype="application/json")
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_init.__doc__ = _lt("Initialize Payment")

    @restapi.method(
        [(["/result"], "GET")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.result.output"),
        auth="public",
        tags=[_lt("Payment Finalization")]
    )
    def payment_result(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            company = api.company_id
            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            result = self._get_transaction_result(tx)

            ResponseOk = self.env.datamodels["payment.result.output"]
            return ResponseOk(**result, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_result.__doc__ = _lt("Payment Result")

    @restapi.webhook(
        input_param=Datamodel("payment.result.webhook"),
        auth="public",
        tags=[_lt("Payment Finalization")]
    )
    def payment_webhook(self):
        pass
    payment_webhook.__doc__ = _lt("Payment Webhook")

    @restapi.method(
        [(["/status"], "GET")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.status.output"),
        auth="public",
        tags=[_lt("Payment Finalization")]
    )
    def payment_status(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            company = api.company_id
            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")
            elif not tx.jetcheckout_order_id:
                return Response("Transaction is being processed, but it has not been done yet.", status=202, mimetype="application/json")

            result = self._query_transaction(tx)

            ResponseOk = self.env.datamodels["payment.status.output"]
            return ResponseOk(**result, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_status.__doc__ = _lt("Payment Status")

    @restapi.method(
        [(["/cancel"], "PUT")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.output"),
        auth="public",
        tags=[_lt("Payment Operation")]
    )
    def payment_cancel(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            company = api.company_id
            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            self._cancel_transaction(tx)

            ResponseOk = self.env.datamodels["payment.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_cancel.__doc__ = _lt("Cancel Payment")

    @restapi.method(
        [(["/refund"], "PUT")],
        input_param=Datamodel("payment.refund.input"),
        output_param=Datamodel("payment.output"),
        auth="public",
        tags=[_lt("Payment Operation")]
    )
    def payment_refund(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            company = api.company_id
            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            self._refund_transaction(tx, params.amount)

            ResponseOk = self.env.datamodels["payment.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_refund.__doc__ = _lt("Refund Payment")

    @restapi.method(
        [(["/expire"], "PUT")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.output"),
        auth="public",
        tags=[_lt("Payment Operation")]
    )
    def payment_expire(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            company = api.company_id
            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            self._expire_transaction(tx)

            ResponseOk = self.env.datamodels["payment.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_expire.__doc__ = _lt("Expire Payment")

    @restapi.method(
        [(["/delete"], "DELETE")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.output"),
        auth="public",
        tags=[_lt("Payment Operation")]
    )
    def payment_delete(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            company = api.company_id
            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            self._delete_transaction(tx)
            return Response("Deleted", status=204, mimetype="application/json")
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_delete.__doc__ = _lt("Delete Payment")

    #
    # PRIVATE METHODS
    #

    def _log_state(self):
        return self.env['payment.paylox.log'].get_state()

    def _log(self, values):
        self.env['payment.paylox.log'].save(values)

    def _get_api(self, apikey, secretkey=False):
        domain = [('api_key', '=', apikey)]
        if secretkey:
            domain.append(('secret_key', '=', secretkey))
        return self.env['payment.acquirer.jetcheckout.api'].sudo().search(domain, limit=1)

    def _get_hash(self, key, hash, id):
        hashed = base64.b64encode(hashlib.sha256(''.join([key.api_key, key.secret_key, str(id)]).encode('utf-8')).digest()).decode('utf-8')
        if hashed != hash:
            return False
        return hash

    def _get_installments(self, api, params, log=None):
        bin = getattr(params, 'bin')
        acquirer = self.env['payment.acquirer']._get_acquirer(company=api.company_id, providers=['jetcheckout'], limit=1)
        if log:
            log.update({'acquirer': acquirer.id})

        url = '%s/api/v1/prepayment/%sinstallment_options' % (acquirer._get_paylox_api_url(), bin and 'bin_' or '')
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_paylox_env(),
            "amount": getattr(params, 'amount', None) or 0,
            "campaign": getattr(params, 'campaign_name', None) or '',
            "currency": getattr(params, 'currency', None) or 'TRY',
            "card_type": getattr(params, 'type', None) or 'AllTypes',
            "language": "tr",
        }
        if bin:
            data.update({"bin": bin})

        response = requests.post(url, data=json.dumps(data), timeout=TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            if result['response_code'] == "00":
                installments = result['installments'] if bin else result['installment_options']
                return {
                    'installments': [{
                        'family': installment['card_family'],
                        'logo': installment['card_family_logo'],
                        'currency': installment['currency'],
                        'campaign': installment['campaign_name'],
                        'period': installment['inst_period'],
                        'type': installment['card_type'],
                        'excluded': None if bin else installment['excluded_bins'],
                        'options': [{
                            'count': i['installment_count'],
                            'amount': i['installment_amount'],
                            'rate_cost': i['cost_rate'],
                            'rate_customer': i['customer_rate'],
                            'plus_count': i['plus_installment'],
                            'plus_desc': i['plus_installment_description'],
                            'min_amount': i['min_amount'],
                            'max_amount': i['max_amount'],
                            'min_rate_customer': i['min_customer_rate'],
                            'max_rate_customer': i['max_customer_rate'],
                        } for i in installment['installments']],
                    } for installment in installments]
                }
            raise Exception(result.get('message', _('An error occured. Please try again.')))
        raise Exception(_('An error occured. Please try again.'))

    def _create_transaction(self, api, hash, params):
        if hasattr(params.partner, 'country'):
            country = self.env['res.country'].sudo().search([('code', '=', params.partner.country)], limit=1)
        else:
            country = False

        if country and hasattr(params.partner, 'state'):
            state = self.env['res.country.state'].sudo().search([('country_id', '=', country.id), ('code', '=', params.partner.state)], limit=1)
        else:
            state = False

        company = api.company_id
        if hasattr(params, 'company'):
            company = self.env['res.company'].sudo().search([('vat', '=', params.company.vat), ('parent_id', '=', company.id)])
            if not company:
                raise Exception('Company cannot be found')

        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1)
        values = {
            'state': 'draft',
            'amount': params.amount,
            'company_id': company.id,
            'acquirer_id': acquirer.id,
            'partner_id': api.partner_id.id,
            'currency_id': company.currency_id.id,
            'jetcheckout_ip_address': params.partner.ip_address,
            'jetcheckout_api_ok': True,
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.id,
            'jetcheckout_api_order': params.order.name,
            'jetcheckout_api_html': getattr(params, 'html', False) or False,
            'jetcheckout_api_contact': getattr(params.partner, 'contact', False) or False,
            'jetcheckout_date_expiration': getattr(params, 'expiration', False) or False,
            'jetcheckout_campaign_name': getattr(params, 'campaign', False) or False,
        }

        methods = getattr(params, 'methods', {})
        if not methods:
            raise Exception('Methods cannot be empty')

        method_ids = []
        method_type = False
        method_types = {
            'virtualPos': 'virtualpos',
            'physicalPos': 'physicalpos',
            'shoppingCredit': 'credit',
            'bankTransfer': 'transfer',
        }
        for method_name, method_value in methods.dump().items():
            if method_name in method_types:
                method_type = method_types[method_name]
                method_values = {
                    'type': method_type,
                    'redirect_url': method_value.get('redirect', False),
                    'webhook_url': method_value.get('webhook', False),
                }
                if method_type == 'physicalpos':
                    physical_pos_ids = tx.company_id.payment_method_physical_pos_ids
                    physical_pos = self.env['payment.method.physicalpos']
                    for i in method_value.get('ids', []):
                        pos = fields.first(physical_pos_ids.filtered(lambda p: p.name == i))
                        if not pos:
                            raise Exception('There is a PoS ID which has not been defined: %s' % i)
                        physical_pos |= pos

                    method_values.update({
                        'type_physicalpos_ids': [(6, 0, physical_pos.ids)]
                    })

                method_ids.append((0, 0, method_values))
        
            values.update({'jetcheckout_payment_type': method_type})
        if len(method_ids) == 1:
            values.update({'jetcheckout_payment_type': method_type})
        values.update({'paylox_api_method_ids': method_ids})

        products = getattr(params.order, 'products', [])
        if products:
            product_ids = []
            prods = self.env['product.product'].sudo()
            for product in products:
                prod = prods.search([
                    #('type', '=', 'product'),
                    ('type', '=', 'consu'),
                    ('default_code', '=', product),
                    '|', ('company_id', '=', company.id),
                        ('company_id', '=', False)
                ])
                if not prod:
                    prod = prods.create({
                        #'type': 'product',
                        'type': 'consu',
                        'name': product.name,
                        'default_code': product.code,
                    })
                product_ids.append((0, 0, {
                    'product_id': prod.id,
                    'qty': product.qty,
                    'name': product.name,
                    'code': product.code,
                    'price': product.price,
                    'categ': getattr(product, 'categ', False) or False,
                    'brand': getattr(product, 'brand', False) or False,
                }))

            values.update({'paylox_product_ids': product_ids})

        tx = self.env['payment.transaction'].sudo().create(values)
        tx.write({
            'partner_name': params.partner.name,
            'partner_vat': params.partner.vat,
            'partner_email': params.partner.email,
            'partner_address': params.partner.address,
            'partner_phone': params.partner.phone,
            'partner_zip': getattr(params.partner, 'zip', '') or '',
            'partner_city': getattr(params.partner, 'city', '') or '',
            'partner_country_id': country and country.id or False,
            'partner_state_id': state and state.id or False,
        })
        return tx

    def _initialize_transaction(self, api, hash, params):
        if hasattr(params.partner, 'country'):
            country = self.env['res.country'].sudo().search([('code', '=', params.partner.country)], limit=1)
        else:
            country = False

        if country and hasattr(params.partner, 'state'):
            state = self.env['res.country.state'].sudo().search([('country_id', '=', country.id), ('code', '=', params.partner.state)], limit=1)
        else:
            state = False

        company = api.company_id
        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1)
        if not acquirer:
            return Response("Acquirer cannot be found", status=400, mimetype="application/json")

        partner = self.env['res.partner'].sudo().search([('vat', '=', params.partner.vat), ('company_id', '=', company.id)]).with_company(company)
        if len(partner) > 1:
            raise Exception('There is more than one partner with VAT %s' % params.partner.vat)

        if partner:
            partner.write({
                'name': params.partner.name,
                'email': params.partner.email,
                'mobile': params.partner.phone,
                'country_id': country and country.id or False,
                'state_id': state and state.id or False,
                'street': getattr(params.partner, 'address', '') or '',
                'city': getattr(params.partner, 'city', '') or '',
                'zip': getattr(params.partner, 'zip', '') or '',
                'ref': getattr(params.partner, 'ref', '') or '',
                'paylox_tax_office': getattr(params.partner, 'taxoffice', False) or False,
            })
        else:
            partner = partner.with_context({'no_vat_validation': True}).create({
                'is_company': True,
                'company_id': company.id,
                'name': params.partner.name,
                'vat': params.partner.vat,
                'email': params.partner.email,
                'mobile': params.partner.phone,
                'country_id': country and country.id or False,
                'state_id': state and state.id or False,
                'street': getattr(params.partner, 'address', '') or '',
                'city': getattr(params.partner, 'city', '') or '',
                'zip': getattr(params.partner, 'zip', '') or '',
                'ref': getattr(params.partner, 'ref', '') or '',
                'paylox_tax_office': getattr(params.partner, 'taxoffice', False) or False,
            })

        values = {
            'state': 'draft',
            'operation': 'online_direct',
            'amount': params.amount,
            'company_id': company.id,
            'acquirer_id': acquirer.id,
            'partner_id': partner.id,
            'currency_id': company.currency_id.id,
            'jetcheckout_api_ok': True,
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.id,
            'jetcheckout_payment_type': 'virtualpos',
            'jetcheckout_ip_address': params.partner.ip_address,
            'jetcheckout_api_success_url': params.successUrl,
            'jetcheckout_api_fail_url': params.failUrl,
            'jetcheckout_campaign_name': getattr(params, 'campaign', False) or False,
        }
        tx = self.env['payment.transaction'].sudo().create(values)
        tx.write({
            'partner_name': params.partner.name,
            'partner_vat': params.partner.vat,
            'partner_email': params.partner.email,
            'partner_phone': params.partner.phone,
            'partner_address': getattr(params.partner, 'address', '') or '',
            'partner_city': getattr(params.partner, 'city', '') or '',
            'partner_zip': getattr(params.partner, 'zip', '') or '',
            'partner_country_id': country and country.id or False,
            'partner_state_id': state and state.id or False,
        })

        fullname = tx.partner_name.split(' ', 1)
        address = []
        if tx.partner_city:
            address.append(tx.partner_city)
        if tx.partner_state_id:
            address.append(tx.partner_state_id.name)
        if tx.partner_country_id:
            address.append(tx.partner_country_id.name)

        year = str(datetime.datetime.now().year)[:2]
        amount_string = '%.0f' % float_round(tx.amount * 100, 0)
        hash = base64.b64encode(hashlib.sha256(''.join([acquirer.jetcheckout_api_key, params.card.number, amount_string, acquirer.jetcheckout_secret_key]).encode('utf-8')).digest()).decode('utf-8')
        base_url = request.httprequest.host
        success_url = '/api/payment/success'
        fail_url = '/api/payment/fail'
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_paylox_env(),
            "campaign_name": params.campaign,
            "amount": amount_string,
            "currency": tx.currency_id.name,
            "installment_count": params.installmentCount,
            "hash_data": hash,
            "language": "tr",
            "card_number": params.card.number,
            "expire_month": params.card.expiry_month,
            "expire_year": year + params.card.expiry_year,
            "card_holder_name": params.card.name,
            "cvc": params.card.cvc,
            "is_3d": True,

            "success_url": "https://%s%s" % (base_url, success_url),
            "fail_url": "https://%s%s" % (base_url, fail_url),
            "order_id": tx.jetcheckout_order_id,
            "customer":  {
                "name": fullname[0],
                "surname": fullname[-1],
                "email": tx.partner_email,
                "id": str(tx.partner_id.id),
                "identity_number": tx.partner_id.vat,
                "phone": tx.partner_phone,
                "ip_address": tx.jetcheckout_ip_address,
                "postal_code": tx.partner_zip,
                "company": tx.partner_id.parent_id and tx.partner_id.parent_id.name or "",
                "address": "%s %s" % (tx.partner_address, "/".join(address)),
                "city": tx.partner_state_id and tx.partner_state_id.name or "",
                "country": tx.partner_country_id and tx.partner_country_id.name or "",
            },
        }

        url = '%s/api/v1/payment' % acquirer._get_paylox_api_url()
        response = requests.post(url, data=json.dumps(data))
        result = response.json()
        if response.status_code == 200:
            values = {
                'status': int(result['response_code']),
                'message': result['message'],
                'suggestion': result.get('suggestion') or '',
                'service_resp_code': result.get('service_resp_code') or '',
                'service_resp_message': result.get('service_resp_message') or '',
                'transaction_id': result.get('transaction_id') or '',
                'url_redirect': '%s/%s' % (result.get('redirect_url') or '', result.get('transaction_id') or ''),
                'virtual_pos_name': result.get('virtual_pos_name') or '',
                'virtual_pos_id': result.get('virtual_pos_id') or '',
                'auth_code': result.get('auth_code') or '',
                'bin_code': result.get('bin_code') or '',
                'installment_count': result.get('installment_count') or 1,
                'currency': result.get('currency') or '',
                'amount': result.get('amount') or 0.0,
                'cost_rate': result.get('expected_cost_rate') or 0.0,
                'cost_amount': result.get('commission_amount') or 0.0,
                'card_type': result.get('card_type') or '',
                'card_program': result.get('card_program') or '',
                'card_family': result.get('card_family') or '',
                'card_bank_eft_code': result.get('card_bank_eft_code') or '',
                'card_bank_name': result.get('card_bank_name') or '',
            }

            txid = result['transaction_id']
            if result['response_code'] == "00307":
                tx.write({
                    'state': 'pending',
                    'callback_hash': hash,
                    'state_message': _('Transaction is pending...'),
                    'acquirer_reference': txid,
                    'jetcheckout_transaction_id': txid,
                    'jetcheckout_data': json.dumps(values, default=str),
                    'last_state_change': datetime.datetime.now(),
                })
            elif result['response_code'] == "00":
                self._process_transaction(tx=tx, **result)
            else:
                message = _('%s (Error Code: %s)') % (result['message'], result['response_code'])
                tx.write({
                    'state': 'error',
                    'state_message': message,
                    'acquirer_reference': txid,
                    'jetcheckout_transaction_id': txid,
                    'last_state_change': datetime.datetime.now(),
                })
            return values
        else:
            return result

    def _process_transaction(self, tx, **result):
        corate = result.get('expected_cost_rate', 0)
        try:
            corate = float(corate)
        except:
            corate = 0

        tx.with_context(domain=request.httprequest.referrer)._paylox_query({
            'successful': result.get('response_code') == '00',
            'pending': result.get('response_code') == '00333',
            'code': result.get('response_code', '') or False,
            'message': result.get('response_message', '') or result.get('message', '') or False,
            'transaction_ref': result.get('transaction_id', False),
            'service_code': result.get('service_resp_code', '') or False,
            'service_message': result.get('service_resp_message', '') or False,
            'service_suggestion': result.get('suggestion', '') or False,
            'amount': result.get('amount', 0) or 0.0,
            'vpos_id': result.get('virtual_pos_id', 0) or 0.0,
            'vpos_name': result.get('virtual_pos_name', '') or False,
            'vpos_code': result.get('auth_code', '') or False,
            'preauth': result.get('preauth', tx.jetcheckout_preauth),
            'postauth': result.get('postauth', tx.jetcheckout_postauth),
            'card_program': result.get('card_program', '') or False,
            'card_family': result.get('card_family', '') or False,
            'card_type': result.get('card_type', '') or False,
            'bin_code': result.get('bin_code', '') or False,
            'commission_amount': result.get('commission_amount', 0) or 0.0,
            'commission_rate': corate,
        })

    def _get_transaction_from_hash(self, company, hash):
        return self.env['payment.transaction'].sudo().search([('company_id', '=', company.id), ('jetcheckout_api_hash', '=', hash)], limit=1)

    def _get_transaction_from_token(self, token):
        return request.env['payment.transaction'].sudo().paylox_get_transaction(token)

    def _get_transaction_result(self, tx):
        return {
            'transaction': {
                'state': tx.state,
                'provider': tx.acquirer_id.provider,
                'virtual_pos_name': tx.jetcheckout_vpos_name or '',
                'order_id': tx.jetcheckout_order_id or '',
                'transaction_id': tx.jetcheckout_transaction_id or '',
                'message': tx.state_message or '',
                'service_code': tx.jetcheckout_service_code or '',
                'service_message': tx.jetcheckout_service_message or '',
                'service_suggestion': tx.jetcheckout_service_suggestion or '',
                'partner': {
                    'name': tx.partner_id.name or '',
                    'ip_address': tx.jetcheckout_ip_address or '',
                },
                'card': {
                    'name': tx.jetcheckout_card_name or '',
                    'number': tx.jetcheckout_card_number or '',
                    'type': tx.jetcheckout_card_type or '',
                    'program': tx.jetcheckout_card_program or '',
                    'family': tx.jetcheckout_card_family or '',
                },
                'credit': {
                    'bank': tx.jetcheckout_payment_type_credit_bank_code or '',
                },
                'amounts': {
                    'amount': tx.amount,
                    'raw': tx.jetcheckout_payment_amount,
                    'fees': tx.fees,
                    'installment': {
                        'amount': tx.jetcheckout_installment_amount,
                        'count': tx.jetcheckout_installment_count,
                        'description': tx.jetcheckout_installment_description,
                    },
                    'commission': {
                        'cost': {
                            'rate': tx.jetcheckout_commission_rate,
                            'amount': tx.jetcheckout_commission_amount,
                        },
                        'customer': {
                            'rate': tx.jetcheckout_customer_rate,
                            'amount': tx.jetcheckout_customer_amount,
                        }
                    },
                },
            }
        }

    def _cancel_transaction(self, tx):
        if not tx.state == 'cancel':
            tx._paylox_cancel()

    def _refund_transaction(self, tx, amount):
        tx._paylox_refund(amount)

    def _expire_transaction(self, tx):
        tx._paylox_expire()

    def _delete_transaction(self, tx):
        tx.unlink()

    def _query_transaction(self, tx):
        vals = tx._paylox_query()
        del vals['currency_id']
        del vals['transaction_id']
        del vals['transaction_ref']
        return vals
