# -*- coding: utf-8 -*-
import base64
import hashlib
import logging

from odoo import _
from odoo.http import Response
from odoo.exceptions import ValidationError
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.controllers.main import RestController
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

RESPONSE = {
    200: {"status": 0, "message": "Success"}
}


class PaymentAPIController(RestController):
    _root_path = "/api/v1/"
    _collection_name = "payment"
    _default_auth = "public"


class PaymentAPIService(Component):
    _inherit = "base.rest.service"
    _name = "payment"
    _usage = "payment"
    _collection = "payment"
    _description = """This API helps you create payments and query their states with your specially generated key"""

    @restapi.method(
        [(["/prepare"], "POST")],
        input_param=Datamodel("payment.prepare.input"),
        output_param=Datamodel("payment.prepare.output"),
        auth="public",
        tags=['Payment Preparation']
    )
    def payment_prepare(self, params):
        """
        Prepare Payment
        """
        try:
            company = self.env.company.id

            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            self._create_transaction(api, hash, params)

            ResponseOk = self.env.datamodels["payment.prepare.output"]
            return ResponseOk(hash=hash, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.method(
        [(["/result"], "GET")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.result.output"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_result(self, params):
        """
        Payment Result
        """
        try:
            company = self.env.company.id

            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            result = self._get_transaction_result(tx)

            ResponseOk = self.env.datamodels["payment.result.output"]
            return ResponseOk(**result, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.method(
        [(["/status"], "GET")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.status.output"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_status(self, params):
        """
        Payment Status
        """
        try:
            company = self.env.company.id
            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

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

    @restapi.method(
        [(["/cancel"], "PUT")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.output"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_cancel(self, params):
        """
        Cancel Payment
        """
        try:
            company = self.env.company.id
            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            self._cancel_transaction(tx)

            ResponseOk = self.env.datamodels["payment.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.method(
        [(["/refund"], "PUT")],
        input_param=Datamodel("payment.refund.input"),
        output_param=Datamodel("payment.output"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_refund(self, params):
        """
        Refund Payment
        """
        try:
            company = self.env.company.id
            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            self._refund_transaction(tx, params.amount)

            ResponseOk = self.env.datamodels["payment.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.method(
        [(["/expire"], "PUT")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.output"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_expire(self, params):
        """
        Expire Payment
        """
        try:
            company = self.env.company.id

            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            self._expire_transaction(tx)

            ResponseOk = self.env.datamodels["payment.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.method(
        [(["/delete"], "DELETE")],
        input_param=Datamodel("payment.credential.hash"),
        output_param=Datamodel("payment.output"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_delete(self, params):
        """
        Delete Payment
        """
        try:
            company = self.env.company.id

            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            tx = self._get_transaction_from_hash(company, params.hash)
            if not tx:
                return Response("Transaction not found", status=404, mimetype="application/json")

            self._delete_transaction(tx)
            return Response("Deleted", status=204, mimetype="application/json")
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    #
    # PRIVATE METHODS
    #

    def _get_api(self, company, apikey, secretkey=False):
        domain = [('company_id', '=', company), ('api_key', '=', apikey)]
        if secretkey:
            domain.append(('secret_key', '=', secretkey))
        return self.env['payment.acquirer.jetcheckout.api'].sudo().search(domain, limit=1)

    def _get_hash(self, key, hash, id):
        hashed = base64.b64encode(hashlib.sha256(''.join([key.api_key, key.secret_key, str(id)]).encode('utf-8')).digest()).decode('utf-8')
        if hashed != hash:
            return False
        return hash

    def _create_transaction(self, api, hash, params):
        if hasattr(params.partner, 'country'):
            country = self.env['res.country'].sudo().search([('code', '=', params.partner.country)], limit=1)
        else:
            country = False

        if country and hasattr(params.partner, 'state'):
            state = self.env['res.country.state'].sudo().search([('country_id', '=', country.id), ('code', '=', params.partner.state)], limit=1)
        else:
            state = False

        sequence_code = 'payment.jetcheckout.transaction'
        name = self.env['ir.sequence'].sudo().next_by_code(sequence_code)
        if not name:
            raise ValidationError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

        codes = hasattr(params, 'methods') and params.methods or []
        method = ''
        providers = []
        for code in codes:
            if code == 'bank':
                providers.append('transfer')
            elif code == 'card':
                providers.append('jetcheckout')
        if len(codes) == 1:
            method = codes[0]

        acquirer = self.env['payment.acquirer']._get_acquirer(company=api.company_id, providers=providers, limit=1)
        products = getattr(params.order, 'products', [])
        values = {
            'reference': name,
            'acquirer_id': acquirer.id,
            'partner_id': api.partner_id.id,
            'amount': params.amount,
            'currency_id': api.company_id.currency_id.id,
            'company_id': api.company_id.id,
            'state': 'draft',
            'jetcheckout_ip_address': params.partner.ip_address,
            'jetcheckout_api_ok': True,
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.id,
            'jetcheckout_api_method': method,
            'jetcheckout_api_contact': getattr(params.partner, 'contact', False) or False,
            'jetcheckout_api_order': params.order.name,
            'jetcheckout_api_card_return_url': params.url.card.result,
            'jetcheckout_date_expiration': getattr(params, 'expiration', False) or False,
            'jetcheckout_campaign_name': getattr(params, 'campaign', False) or False,
        }

        if products:
            values.update({'jetcheckout_api_product': ','.join(list(map(lambda x: x.name, products)))})

        if getattr(params.url, 'bank', None):
            values.update({'jetcheckout_api_bank_return_url': params.url.bank.result})
            if getattr(params.url.bank, 'webhook', None):
                values.update({'jetcheckout_api_bank_webhook_url': params.url.bank.webhook})

        tx = self.env['payment.transaction'].sudo().create(values)
        tx.write({
            'partner_name': params.partner.name,
            'partner_vat': params.partner.vat,
            'partner_email': params.partner.email,
            'partner_address': params.partner.address,
            'partner_phone': params.partner.phone,
            'partner_zip': params.partner.zip,
            'partner_city': getattr(params.partner, 'city', '') or '',
            'partner_country_id': country and country.id or False,
            'partner_state_id': state and state.id or False,
        })

    def _get_transaction_from_hash(self, company, hash):
        return self.env['payment.transaction'].sudo().search([('company_id', '=', company), ('jetcheckout_api_hash', '=', hash)], limit=1)

    def _get_transaction_from_token(self, token):
        return self.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', token)], limit=1)

    def _get_transaction_result(self, tx):
        return {
            'transaction': {
                'state': tx.state,
                'provider': tx.acquirer_id.provider,
                'virtual_pos_name': tx.jetcheckout_vpos_name or '',
                'order_id': tx.jetcheckout_order_id or '',
                'transaction_id': tx.jetcheckout_transaction_id or '',
                'message': tx.state_message if not tx.state == 'done' else _('Transaction is successful'),
                'partner': {
                    'name': tx.partner_id.name or '',
                    'ip_address': tx.jetcheckout_ip_address or '',
                },
                'card': {
                    'name': tx.jetcheckout_card_name or '',
                    'number': tx.jetcheckout_card_number or '',
                    'type': tx.jetcheckout_card_type or '',
                    'family': tx.jetcheckout_card_family or '',
                },
                'amounts': {
                    'amount': tx.amount,
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
            tx._jetcheckout_cancel()

    def _refund_transaction(self, tx, amount):
        tx._jetcheckout_refund(amount)

    def _expire_transaction(self, tx):
        tx._jetcheckout_expire()

    def _delete_transaction(self, tx):
        tx.unlink()

    def _query_transaction(self, tx):
        vals = tx._jetcheckout_query()
        del vals['currency_id']
        return vals
