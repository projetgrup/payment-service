# -*- coding: utf-8 -*-
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.controllers.main import RestController
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component
from odoo.exceptions import ValidationError
from odoo import _
import base64
import hashlib

RESPONSE = {
    "success": {
        "response_code": 0,
        "response_message": "İşlem başarılı",
    },
    "no_api_key": {
        "response_code": 9,
        "response_message": "API anahtarı bulunamadı",
    },
    "no_hash_match": {
        "response_code": 8,
        "response_message": "Hash geçersiz",
    },
    "no_transaction": {
        "response_code": 7,
        "response_message": "İşlem bulunamadı",
    },
    "incomplete_transaction": {
        "response_code": 8,
        "response_message": "İşlem henüz tamamlanmamış görünüyor",
    },
    "exception": {
        "response_code": -1,
        "response_message": "Sunucu hatası",
    },
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
        Response = self.env.datamodels["payment.prepare.output"]
        try:
            company = self.env.company.id

            api = self._check_auth(company, params.application_key)
            if not api:
                return Response(**RESPONSE['no_api_key'])

            hash = self._check_hash(api, params.hash, params.id)
            if not hash:
                return Response(**RESPONSE['no_hash_match'])

            self._create_transaction(api, hash, params)
            return Response(hash=params.hash, **RESPONSE['success'])
        except Exception as e:
            exception = {**RESPONSE['exception']}
            exception['response_message'] = str(e)
            return Response(**exception)

    @restapi.method(
        [(["/result"], "POST")],
        input_param=Datamodel("payment.hash.input"),
        output_param=Datamodel("payment.result.output"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_result(self, params):
        """
        Payment Result
        """
        Response = self.env.datamodels["payment.result.output"]
        try:
            company = self.env.company.id

            api = self._check_auth(company, params.application_key)
            if not api:
                return Response(**RESPONSE['no_api_key'])

            tx = self._get_transaction(params.hash)
            if not tx:
                return Response(**RESPONSE['no_transaction'])

            result = self._get_payment_result(tx)
            return Response(**result,**RESPONSE['success'])
        except Exception as e:
            exception = {**RESPONSE['exception']}
            exception['response_message'] = str(e)
            return Response(**exception)

    @restapi.method(
        [(["/status"], "POST")],
        input_param=Datamodel("payment.hash.input"),
        output_param=Datamodel("payment.status.output"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_status(self, params):
        """
        Payment Status
        """
        Response = self.env.datamodels["payment.status.output"]
        try:
            company = self.env.company.id
            api = self._check_auth(company, params.application_key)
            if not api:
                return Response(**RESPONSE['no_api_key'])

            tx = self._get_transaction(params.hash)
            if not tx:
                return Response(**RESPONSE['no_transaction'])
            elif not tx.jetcheckout_order_id:
                return Response(**RESPONSE['incomplete_transaction'])
                

            result = self._query_payment(tx)
            return Response(**result, **RESPONSE['success'])
        except Exception as e:
            exception = {**RESPONSE['exception']}
            exception['response_message'] = str(e)
            return Response(**exception)

    @restapi.method(
        [(["/cancel"], "POST")],
        input_param=Datamodel("payment.token.input"),
        output_param=Datamodel("payment.response"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_cancel(self, params):
        """
        Cancel Payment
        """
        Response = self.env.datamodels["payment.response"]
        try:
            company = self.env.company.id
            api = self._check_auth(company, params.application_key)
            if not api:
                return Response(**RESPONSE['no_api_key'])

            tx = self._get_transaction_from_token(params.token)
            if not tx:
                return Response(**RESPONSE['no_transaction'])

            self._cancel_payment(tx)
            return Response(**RESPONSE['success'])
        except Exception as e:
            exception = {**RESPONSE['exception']}
            exception['response_message'] = str(e)
            return Response(**exception)

    @restapi.method(
        [(["/refund"], "POST")],
        input_param=Datamodel("payment.refund.input"),
        output_param=Datamodel("payment.response"),
        auth="public",
        tags=['Payment Operation']
    )
    def payment_refund(self, params):
        """
        Refund Payment
        """
        Response = self.env.datamodels["payment.response"]
        try:
            company = self.env.company.id
            api = self._check_auth(company, params.application_key)
            if not api:
                return Response(**RESPONSE['no_api_key'])

            tx = self._get_transaction_from_token(params.token)
            if not tx:
                return Response(**RESPONSE['no_transaction'])

            self._refund_payment(tx, params.amount)
            return Response(**RESPONSE['success'])
        except Exception as e:
            exception = {**RESPONSE['exception']}
            exception['response_message'] = str(e)
            return Response(**exception)

    # PRIVATE METHODS
    def _check_auth(self, company, apikey, secretkey=False):
        domain = [('company_id','=',company),('api_key','=',apikey)]
        if secretkey:
            domain.append(('secret_key','=',secretkey))
        return self.env["payment.acquirer.jetcheckout.api"].sudo().search(domain, limit=1)

    def _check_hash(self, key, hash, id):
        hashed = base64.b64encode(hashlib.sha256(''.join([key.api_key, key.secret_key, str(id)]).encode('utf-8')).digest()).decode('utf-8')
        if hashed != hash:
            return False
        return hash

    def _create_transaction(self, api, hash, params):
        country = self.env['res.country'].sudo().search([('code','=',params.partner['country_code'])], limit=1) if 'country_code' in params.partner else False
        if country:
            state = self.env['res.country.state'].sudo().search([('country_id','=',country.id),('code','=',params.partner['state_code'])], limit=1) if 'state_code' in params.partner else False
        else:
            state = False

        sequence_code = 'payment.jetcheckout.transaction'
        name = self.env['ir.sequence'].sudo().next_by_code(sequence_code)
        if not name:
            raise ValidationError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

        acquirer = self.env['payment.acquirer']._get_acquirer(company=self.env.company, providers=['transfer'], limit=1)
        tx = self.env['payment.transaction'].sudo().create({
            'reference': name,
            'acquirer_id': acquirer.id,
            'partner_id': api.partner_id.id,
            'amount': params.amount,
            'currency_id': api.company_id.currency_id.id,
            'company_id': api.company_id.id,
            'state': 'draft',
            'jetcheckout_api_contact': params.partner['contact'],
            'jetcheckout_ip_address': params.partner['ip_address'],
            'jetcheckout_api_order': params.order['name'],
            'jetcheckout_api_product': params.product['name'],
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.id,
            'jetcheckout_api_bank_return_url': params.bank_return_url,
            'jetcheckout_api_bank_webhook_url': params.bank_webhook_url,
            'jetcheckout_api_card_return_url': params.card_return_url,
        })
        tx.write({
            'partner_name': params.partner['name'],
            'partner_email': params.partner['email'],
            'partner_address': params.partner['address'],
            'partner_phone': params.partner['phone'],
            'partner_zip': params.partner['zip'],
            'partner_city': params.partner['city'],
            'partner_country_id': country and country.id or False,
            'partner_state_id': state and state.id or False,
        })

    def _get_transaction(self, hash):
        return self.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '=', hash)], limit=1)

    def _get_transaction_from_token(self, token):
        return self.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', token)], limit=1)

    def _get_payment_result(self, tx):
        return {
            'provider': tx.acquirer_id.provider,
            'state': tx.state,
            'fees': tx.fees,
            'message': tx.state_message if not tx.state == 'done' else 'İşlem Başarılı',
            'ip_address': tx.jetcheckout_ip_address or '',
            'card_name': tx.jetcheckout_card_name or '',
            'card_number': tx.jetcheckout_card_number or '',
            'card_type': tx.jetcheckout_card_type or '',
            'card_family': tx.jetcheckout_card_family or '',
            'vpos_name': tx.jetcheckout_vpos_name or '',
            'order_id': tx.jetcheckout_order_id or '',
            'transaction_id': tx.jetcheckout_transaction_id or '',
            'payment_amount': tx.jetcheckout_payment_amount,
            'installment_count': tx.jetcheckout_installment_count,
            'installment_desc': tx.jetcheckout_installment_description,
            'installment_amount': tx.jetcheckout_installment_amount,
            'commission_rate': tx.jetcheckout_commission_rate,
            'commission_amount': tx.jetcheckout_commission_amount,
            'customer_rate': tx.jetcheckout_customer_rate,
            'customer_amount': tx.jetcheckout_customer_amount,
        }

    def _cancel_payment(self, tx):
        tx._jetcheckout_cancel()

    def _refund_payment(self, tx, amount):
        tx._jetcheckout_refund(amount)

    def _query_payment(self, tx):
        vals = tx._jetcheckout_query()
        del vals['currency_id']
        return vals
