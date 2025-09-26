# -*- coding: utf-8 -*-
import json
import time
import base64
import hashlib
import logging
import traceback
from urllib.parse import quote

from odoo.http import Response, request
from odoo.tools.translate import _, _lt
from odoo.exceptions import MissingError, ValidationError, UserError
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

PAGE_SIZE = 100
RESPONSE = {
    200: {"status": 0, "message": "Success"}
}

class OrderCheckoutAPIService(Component):
    _inherit = "base.rest.service"
    _name = "Order Checkout"
    _usage = "oco"
    _collection = "payment"
    _description = """This API helps you connect oco payment system with your specially generated key"""

    @restapi.method(
        [(["/payment/create"], "POST")],
        input_param=Datamodel("oco.payment.create.request"),
        output_param=Datamodel("oco.payment.create.response"),
        auth="public",
        tags=['Payments']
    )
    def create_payments(self, params):
        """
        Create Payments
        """
        try:
            log = None
            loggable = self._log_state()
            if loggable:
                log = {
                    'service': 'api_oco_create_payment',
                    'now': time.time(),
                    'method': 'post',
                    'url': '/oco/payment/create',
                    'request': json.dumps(params.dump(), indent=4, default=str, ensure_ascii=False),
                }
        except:
            log = None
            loggable = None

        try:
            company = self.env.company.id
            if loggable:
                log.update({
                    'company': company,
                })

            api = self._get_api(company, params.apikey)
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

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                status, message = 401, _('Hash does not match.')
                if loggable:
                    log.update({
                        'code': status,
                        'status': False,
                        'message': message,
                        'response': message,
                    })
                    self._log(log)
                return Response(message, status=status, mimetype="application/json")


            tx = self._create_transaction(api, hash, params)
            id = tx.jetcheckout_order_id
            url = 'https://%s/payment?=%s' % (request.httprequest.host, quote(hash))
            response = dict(id=id, url=url, **RESPONSE[200])

            if loggable:
                log.update({
                    'code': 200,
                    'status': True,
                    'message': _('Success'),
                    'transaction': tx.id,
                    'acquirer': tx.acquirer_id.id,
                    'env': tx.acquirer_id._get_paylox_env(),
                    'response': json.dumps(response, indent=4, default=str, ensure_ascii=False),
                })
                self._log(log)

            ResponseOk = self.env.datamodels["oco.payment.create.response"]
            return ResponseOk(**response)

        except Exception as e:
            status, message = 500, _('An error occured')
            debug = traceback.format_exc()
            if loggable:
                log.update({
                    'code': status,
                    'status': False,
                    'message': message,
                    'debug': debug,
                    'response': str(e),
                })
                self._log(log)

            _logger.error(debug)
            return Response(message, status=status, mimetype="application/json")

    create_payments.__doc__ = _lt("Prepare Payment")

    @restapi.method(
        [(["/payment/cancel"], "POST")],
        input_param=Datamodel("oco.payment.cancel.request"),
        output_param=Datamodel("oco.payment.cancel.response"),
        auth="public",
        tags=['Payments']
    )
    def cancel_payments(self, params):
        """
        Cancel Payments
        """
        try:
            log = None
            loggable = self._log_state()
            if loggable:
                log = {
                    'service': 'api_oco_cancel_payment',
                    'now': time.time(),
                    'method': 'post',
                    'url': '/oco/payment/cancel',
                    'request': json.dumps(params.dump(), indent=4, default=str, ensure_ascii=False),
                }
        except:
            log = None
            loggable = None

        try:
            company = self.env.company.id
            if loggable:
                log.update({
                    'company': company,
                })

            api = self._get_api(company, params.apikey)
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

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                status, message = 401, _('Hash does not match.')
                if loggable:
                    log.update({
                        'code': status,
                        'status': False,
                        'message': message,
                        'response': message,
                    })
                    self._log(log)
                return Response(message, status=status, mimetype="application/json")

            self._cancel_transaction(api, params, log=log)
            response = dict(**RESPONSE[200])

            if loggable:
                log.update({
                    'code': 200,
                    'status': True,
                    'message': _('Success'),
                    'response': json.dumps(response, indent=4, default=str, ensure_ascii=False),
                })
                self._log(log)

            ResponseOk = self.env.datamodels["oco.payment.cancel.response"]
            return ResponseOk(**response)

        except Exception as e:
            status, message = 500, _('An error occured')
            debug = traceback.format_exc()
            if loggable:
                log.update({
                    'code': status,
                    'status': False,
                    'message': message,
                    'debug': debug,
                    'response': str(e),
                })
                self._log(log)

            _logger.error(debug)
            return Response(message, status=status, mimetype="application/json")

    cancel_payments.__doc__ = _lt("Cancel Payment")

    @restapi.method(
        [(["/payment/refund"], "POST")],
        input_param=Datamodel("oco.payment.refund.request"),
        output_param=Datamodel("oco.payment.refund.response"),
        auth="public",
        tags=['Payments']
    )
    def refund_payments(self, params):
        """
        Refund Payments
        """
        try:
            log = None
            loggable = self._log_state()
            if loggable:
                log = {
                    'service': 'api_oco_refund_payment',
                    'now': time.time(),
                    'method': 'post',
                    'url': '/oco/payment/refund',
                    'request': json.dumps(params.dump(), indent=4, default=str, ensure_ascii=False),
                }
        except:
            log = None
            loggable = None

        try:
            company = self.env.company.id
            if loggable:
                log.update({
                    'company': company,
                })

            api = self._get_api(company, params.apikey)
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

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                status, message = 401, _('Hash does not match.')
                if loggable:
                    log.update({
                        'code': status,
                        'status': False,
                        'message': message,
                        'response': message,
                    })
                    self._log(log)
                return Response(message, status=status, mimetype="application/json")

            self._refund_transaction(api, params, log=log)
            response = dict(**RESPONSE[200])

            if loggable:
                log.update({
                    'code': 200,
                    'status': True,
                    'message': _('Success'),
                    'response': json.dumps(response, indent=4, default=str, ensure_ascii=False),
                })
                self._log(log)

            ResponseOk = self.env.datamodels["oco.payment.refund.response"]
            return ResponseOk(**response)

        except Exception as e:
            status, message = 500, _('An error occured')
            debug = traceback.format_exc()
            if loggable:
                log.update({
                    'code': status,
                    'status': False,
                    'message': message,
                    'debug': debug,
                    'response': str(e),
                })
                self._log(log)

            _logger.error(debug)
            return Response(message, status=status, mimetype="application/json")

    refund_payments.__doc__ = _lt("Refund Payment")

    @restapi.method(
        [(["/payment/postauth"], "POST")],
        input_param=Datamodel("oco.payment.postauth.request"),
        output_param=Datamodel("oco.payment.postauth.response"),
        auth="public",
        tags=['Payments']
    )
    def postauth_payments(self, params):
        """
        Postauth Payments
        """
        try:
            log = None
            loggable = self._log_state()
            if loggable:
                log = {
                    'service': 'api_oco_postauth_payment',
                    'now': time.time(),
                    'method': 'post',
                    'url': '/oco/payment/postauth',
                    'request': json.dumps(params.dump(), indent=4, default=str, ensure_ascii=False),
                }
        except:
            log = None
            loggable = None

        try:
            company = self.env.company.id
            if loggable:
                log.update({
                    'company': company,
                })

            api = self._get_api(company, params.apikey)
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

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                status, message = 401, _('Hash does not match.')
                if loggable:
                    log.update({
                        'code': status,
                        'status': False,
                        'message': message,
                        'response': message,
                    })
                    self._log(log)
                return Response(message, status=status, mimetype="application/json")

            self._postauth_transaction(api, params, log=log)
            response = dict(**RESPONSE[200])

            if loggable:
                log.update({
                    'code': 200,
                    'status': True,
                    'message': _('Success'),
                    'response': json.dumps(response, indent=4, default=str, ensure_ascii=False),
                })
                self._log(log)

            ResponseOk = self.env.datamodels["oco.payment.postauth.response"]
            return ResponseOk(**response)

        except Exception as e:
            status, message = 500, _('An error occured')
            debug = traceback.format_exc()
            if loggable:
                log.update({
                    'code': status,
                    'status': False,
                    'message': message,
                    'debug': debug,
                    'response': str(e),
                })
                self._log(log)

            _logger.error(debug)
            return Response(message, status=status, mimetype="application/json")

    postauth_payments.__doc__ = _lt("Postauth Payment")

    @restapi.webhook(
        input_param=Datamodel("oco.payment.webhook"),
        auth="public",
        tags=['Payments']
    )
    def webhook_payments(self):
        """
        Postauth Payments
        """
        pass
    webhook_payments.__doc__ = _lt("Payment Webhook")

    @restapi.method(
        [(["/payment/query"], "GET")],
        input_param=Datamodel("oco.payment.query.request"),
        output_param=Datamodel("oco.payment.query.response"),
        auth="public",
        tags=['Payments']
    )
    def query_payments(self, params):
        """
        Query Payments
        """
        try:
            log = None
            loggable = self._log_state()
            if loggable:
                log = {
                    'service': 'api_oco_query_payment',
                    'now': time.time(),
                    'method': 'get',
                    'url': '/oco/payment/query',
                    'request': json.dumps(params.dump(), indent=4, default=str, ensure_ascii=False),
                }
        except:
            log = None
            loggable = None

        try:
            company = self.env.company.id
            if loggable:
                log.update({
                    'company': company,
                })

            api = self._get_api(company, params.apikey)
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

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                status, message = 401, _('Hash does not match.')
                if loggable:
                    log.update({
                        'code': status,
                        'status': False,
                        'message': message,
                        'response': message,
                    })
                    self._log(log)
                return Response(message, status=status, mimetype="application/json")

            result = self._query_transaction(api, params, log=log)
            response = dict(**result, **RESPONSE[200])

            if loggable:
                log.update({
                    'code': 200,
                    'status': True,
                    'message': _('Success'),
                    'response': json.dumps(response, indent=4, default=str, ensure_ascii=False),
                })
                self._log(log)

            ResponseOk = self.env.datamodels["oco.payment.query.response"]
            return ResponseOk(**response)

        except Exception as e:
            status, message = 500, _('An error occured')
            debug = traceback.format_exc()
            if loggable:
                log.update({
                    'code': status,
                    'status': False,
                    'message': message,
                    'debug': debug,
                    'response': str(e),
                })
                self._log(log)

            _logger.error(debug)
            return Response(message, status=status, mimetype="application/json")

    query_payments.__doc__ = _lt("Query Payment")

    @restapi.method(
        [(["/report/transactions"], "GET")],
        input_param=Datamodel("oco.report.transactions.request"),
        output_param=Datamodel("oco.report.transactions.response"),
        auth="public",
        tags=['Reports']
    )
    def _report_transactions(self, params):
        """
        Transaction Reports
        """
        try:
            log = None
            loggable = self._log_state()
            if loggable:
                log = {
                    'service': 'api_oco_report_transactions',
                    'now': time.time(),
                    'method': 'get',
                    'url': '/oco/report/transactions',
                    'request': json.dumps(params.dump(), indent=4, default=str, ensure_ascii=False),
                }
        except:
            log = None
            loggable = None

        try:
            company = self.env.company.id
            if loggable:
                log.update({
                    'company': company,
                })

            api = self._get_api(company, params.apikey)
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

            hash = self._get_hash(api, params.hash, '')
            if not hash:
                status, message = 401, _('Hash does not match.')
                if loggable:
                    log.update({
                        'code': status,
                        'status': False,
                        'message': message,
                        'response': message,
                    })
                    self._log(log)
                return Response(message, status=status, mimetype="application/json")

            try:
                result = self._report_transactions(api, params, log=log)
            except MissingError as e:
                return Response(str(e), status=404)
            except ValidationError as e:
                return Response(str(e), status=400)
            except UserError as e:
                return Response(str(e), status=400)

            response = dict(**result, **RESPONSE[200])

            if loggable:
                log.update({
                    'code': 200,
                    'status': True,
                    'message': _('Success'),
                    'response': json.dumps(response, indent=4, default=str, ensure_ascii=False),
                })
                self._log(log)

            ResponseOk = self.env.datamodels["oco.report.transactions.response"]
            return ResponseOk(**response)

        except Exception as e:
            status, message = 500, _('An error occured')
            debug = traceback.format_exc()
            if loggable:
                log.update({
                    'code': status,
                    'status': False,
                    'message': message,
                    'debug': debug,
                    'response': str(e),
                })
                self._log(log)

            _logger.error(debug)
            return Response(message, status=status, mimetype="application/json")

    report_transactions.__doc__ = _lt("Transactions")

    #
    # PRIVATE METHODS
    #

    def _log_state(self):
        return self.env['payment.paylox.log'].get_state()

    def _log(self, values):
        self.env['payment.paylox.log'].save(values)

    def _get_api(self, company, apikey, secretkey=False):
        domain = [('company_id', '=', company), ('api_key', '=', apikey), ('perm_payment', '=', True)]
        if secretkey:
            domain.append(('secret_key', '=', secretkey))
        return self.env['payment.acquirer.jetcheckout.api'].sudo().search(domain, limit=1)

    def _get_hash(self, key, hash, id):
        hashed = base64.b64encode(hashlib.sha256(''.join([key.api_key, key.secret_key, str(id)]).encode('utf-8')).digest()).decode('utf-8')
        if hashed != hash:
            return False
        return hash

    def _create_transaction(self, api, hash, params):
        if getattr(params.partner, 'country', None):
            country = self.env['res.country'].sudo().search([('code', '=', params.partner.country)], limit=1)
        else:
            country = False

        if country and getattr(params.partner, 'state', None):
            state = self.env['res.country.state'].sudo().search([('country_id', '=', country.id), ('code', '=', params.partner.state)], limit=1)
        else:
            state = False

        company = api.company_id
        if getattr(params, 'company', None):
            company = self.env['res.company'].sudo().search([('vat', '=', params.company.vat), ('parent_id', '=', company.id)])
            if not company:
                raise Exception('Company cannot be found')

        partner = api.partner_id
        partner_field = api.company_id._get_payment_partner_unique_field()
        if getattr(params, 'partner', None):
            if not hasattr(params.partner, partner_field):
                raise Exception('Field "%s" must be set' % partner_field)

            partner = self.env['res.partner'].sudo().search([(partner_field, '=', getattr(params.partner, partner_field)), ('company_id', '=', company.id)]).with_company(company)
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
                partner = partner.with_context({'no_vat_validation': True, 'active_system': 'oco'}).create({
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

        acquirer = self._get_acquirer(company=company)
        values = {
            'acquirer_id': acquirer.id,
            'partner_id': partner.id,
            'amount': getattr(params.order, 'amount', 0),
            'currency_id': company.currency_id.id,
            'company_id': company.id,
            'state': 'draft',
            'jetcheckout_api_ok': True,
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.id,
            'jetcheckout_api_method': 'card',
            'jetcheckout_api_order': params.order.name,
            'jetcheckout_api_card_redirect_url': params.url.redirect,
            'jetcheckout_api_card_result_url': 'https://%s/payment/card/result' % request.httprequest.host,
            'jetcheckout_api_html': getattr(params, 'html', False) or False,
            'jetcheckout_api_contact': getattr(params.partner, 'contact', False) or False,
            'jetcheckout_date_expiration': getattr(params, 'expiration', False) or False,
            'jetcheckout_campaign_name': getattr(params, 'campaign', False) or False,
            'jetcheckout_ip_address': request.httprequest.remote_addr,
            'jetcheckout_preauth': getattr(params, 'preauth', False) or False,
        }

        products = getattr(params.order, 'products', [])
        if products:
            amount = 0
            product_ids = []
            prods = self.env['product.product'].sudo().with_context(system='oco')
            for product in products:
                prod = prods.search([
                    #('type', '=', 'product'),
                    ('type', '=', 'consu'),
                    ('default_code', '=', product.code),
                    ('company_id', '=', api.company_id.id)
                ], limit=1)
                if not prod:
                    prod = prods.create({
                        #'type': 'product',
                        'type': 'consu',
                        'name': product.name,
                        'default_code': product.code,
                        'company_id': api.company_id.id,
                    })
                product_ids.append((0, 0, {
                    'product_id': prod.id,
                    'name': product.name,
                    'code': product.code,
                    'qty': product.qty,
                    'price': product.price,
                }))
                amount += product.qty * product.price
            values.update({
                #'amount': amount,
                'paylox_product_ids': product_ids,
            })
            #values.update({'jetcheckout_api_product': ','.join(list(map(lambda x: x.name, products)))})

        tx = self.env['payment.transaction'].sudo().with_company(company).create(values)
        tx.write({
            'partner_name': params.partner.name,
            'partner_vat': params.partner.vat,
            'partner_email': params.partner.email,
            'partner_phone': params.partner.phone,
            'partner_address': getattr(params.partner, 'address', '') or '',
            'partner_zip': getattr(params.partner, 'zip', '') or '',
            'partner_city': getattr(params.partner, 'city', '') or '',
            'partner_country_id': country and country.id or False,
            'partner_state_id': state and state.id or False,
        })
        return tx

    def _get_acquirer(self, company):
        return self.env['payment.acquirer'].sudo().with_company(company)._get_acquirer(company=company, providers=['jetcheckout'], limit=1, raise_exception=True)

    def _cancel_transaction(self, api, params, log=None):
        tx = request.env['payment.transaction'].sudo().paylox_get_transaction(str(params.id))
        if not tx:
            raise Exception('Transaction cannot be found')

        if log:
            log.update({
                'transaction': tx.id,
                'acquirer': tx.acquirer_id.id,
                'env': tx.acquirer_id._get_paylox_env(),
            })

        tx._paylox_cancel()

    def _refund_transaction(self, api, params, log=None):
        tx = request.env['payment.transaction'].sudo().paylox_get_transaction(str(params.id))
        if not tx:
            raise Exception('Transaction cannot be found')
        
        if log:
            log.update({
                'transaction': tx.id,
                'acquirer': tx.acquirer_id.id,
                'env': tx.acquirer_id._get_paylox_env(),
            })

        tx._paylox_refund(params.amount)

    def _postauth_transaction(self, api, params, log=None):
        tx = request.env['payment.transaction'].sudo().paylox_get_transaction(str(params.id))
        if not tx:
            raise Exception('Transaction cannot be found')

        if log:
            log.update({
                'transaction': tx.id,
                'acquirer': tx.acquirer_id.id,
                'env': tx.acquirer_id._get_paylox_env(),
            })

        tx.with_context(amount=params.amount)._send_capture_request()

    def _query_transaction(self, api, params, log=None):
        tx = request.env['payment.transaction'].sudo().paylox_get_transaction(str(params.id))
        if not tx:
            raise Exception('Transaction cannot be found')

        if log:
            log.update({
                'transaction': tx.id,
                'acquirer': tx.acquirer_id.id,
                'env': tx.acquirer_id._get_paylox_env(),
            })

        result = tx._paylox_query()
        del result['currency_id']
        del result['transaction_id']
        del result['transaction_ref']

        if result.get('successful'):
            result.update({
                'receipt_url': 'https://%s/payment/card/report/receipt/%s' % (request.httprequest.host, tx.jetcheckout_order_id),
                'conveyance_url': 'https://%s/payment/card/report/conveyance/%s' % (request.httprequest.host, tx.jetcheckout_order_id),
            })
        return result

    def _report_transactions(self, api, params, log=None):
        txs = request.env['payment.transaction'].sudo().search([
            ('state', '=', 'done'),
            ('create_date', '>=', params.dateStart),
            ('create_date', '<=', params.dateEnd),
            '|',
            ('company_id', '=', api.company_id.id),
            ('company_id.parent_id', '=', api.company_id.id),
        ])
        if not txs:
            raise MissingError('Transaction cannot be found')

        return {
            'result': [{
                'logDate': tx.create_date.strftime('%Y%m%d') or None,
                'logTime': tx.create_date.strftime('%H%M%S') or None,
                'paymentId': tx.jetcheckout_order_id or None,
                'postAmount': tx.jetcheckout_postauth_amount or 0.0,
                'bankName': 'iyzico',
                'cardNumber': tx.jetcheckout_card_number or None,
                'installment': tx.jetcheckout_installment_description or '0',
                'outletNumber': tx.partner_ref or None,
                'channel': 'indirect',
                'paymentProvider': 'iyzico',
                'vkn': tx.company_id.vat or None,
                'distName': tx.company_id.name or None,
            } for tx in txs]
        }
