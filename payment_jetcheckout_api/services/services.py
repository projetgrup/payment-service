# -*- coding: utf-8 -*-
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.controllers.main import RestController
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component
from odoo.exceptions import ValidationError
from odoo import _
import base64
import hashlib

import logging
_logger = logging.getLogger(__name__)

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
    "exception": {
        "response_code": -1,
        "response_message": "Sunucu hatası",
    },
}


class PaymentAPIController(RestController):
    _root_path = "/api/v1/"
    _collection_name = "payment.api.services"
    _default_auth = "public"


class PaymentAPIService(Component):
    _inherit = "base.rest.service"
    _name = "payment.api.service"
    _usage = "payment"
    _collection = "payment.api.services"
    _description = """Payment API Services"""

    @restapi.method(
        [(["/prepare"], "POST")],
        input_param=Datamodel("payment.prepare.input"),
        output_param=Datamodel("payment.prepare.output"),
        auth="public",
    )
    def payment_prepare(self, params):
        """
        Prepare Payment
        """
        PrepareResponse = self.env.datamodels["payment.prepare.output"]
        try:
            company = self.env.company.id

            api = self._check_auth(company, params.application_key)
            if not api:
                return PrepareResponse(**RESPONSE['no_api_key'])

            hash = self._check_hash(api, params.hash, params.id)
            if not hash:
                return PrepareResponse(**RESPONSE['no_hash_match'])

            self._create_transaction(api, hash, params)
            return PrepareResponse(hash=params.hash, **RESPONSE['success'])
        except Exception as e:
            _logger.error(str(e))
            return PrepareResponse(**RESPONSE['exception'])

    @restapi.method(
        [(["/result"], "POST")],
        input_param=Datamodel("payment.result.input"),
        output_param=Datamodel("payment.result.output"),
        auth="public",
    )
    def payment_result(self, params):
        """
        Get Payment Result
        """
        ResultResponse = self.env.datamodels["payment.result.output"]
        try:
            company = self.env.company.id

            api = self._check_auth(company, params.application_key)
            if not api:
                return ResultResponse(**RESPONSE['no_api_key'])

            tx = self._get_transaction(params.hash)
            if not tx:
                return ResultResponse(**RESPONSE['no_transaction'])

            result = self._get_payment_result(tx)
            return ResultResponse(**result,**RESPONSE['success'])
        except Exception as e:
            _logger.error(str(e))
            return ResultResponse(**RESPONSE['exception'])

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
        country = self.env['res.country'].sudo().search([('code','=',params.customer['country_code'])], limit=1) if 'country_code' in params.customer else False
        if country:
            state = self.env['res.country.state'].sudo().search([('country_id','=',country.id),('code','=',params.customer['state_code'])], limit=1) if 'state_code' in params.customer else False
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
            'partner_authorized': params.customer['authorized'],
            'jetcheckout_ip_address': params.customer['ip_address'],
            'jetcheckout_api_ref': params.order['name'],
            'jetcheckout_api_product': params.product['name'],
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_tx': params.id,
            'jetcheckout_api_return_url': params.return_url,
        })
        tx.write({
            'partner_name': params.customer['name'],
            'partner_email': params.customer['email'],
            'partner_address': params.customer['address'],
            'partner_phone': params.customer['phone'],
            'partner_zip': params.customer['zip'],
            'partner_city': params.customer['city'],
            'partner_country_id': country and country.id or False,
            'partner_state_id': state and state.id or False,
        })

    def _get_transaction(self, hash):
        return self.env['payment.transaction'].sudo().search([('jetcheckout_api_hash', '=', hash)], limit=1)

    def _get_payment_result(self, tx):
        return {
            'state': tx.state,
            'fees': tx.fees,
            'ip_address': tx.jetcheckout_ip_address or '',
            'card_name': tx.jetcheckout_card_name or '',
            'card_number': tx.jetcheckout_card_number or '',
            'card_type': tx.jetcheckout_card_type or '',
            'vpos_name': tx.jetcheckout_vpos_name or '',
            'order_id': tx.jetcheckout_order_id or '',
            'transaction_id': tx.jetcheckout_transaction_id or '',
            'payment_amount': tx.jetcheckout_payment_amount,
            'installment_count': tx.jetcheckout_installment_count,
            'installment_amount': tx.jetcheckout_installment_amount,
            'commission_rate': tx.jetcheckout_commission_rate,
            'commission_amount': tx.jetcheckout_commission_amount,
            'customer_rate': tx.jetcheckout_customer_rate,
            'customer_amount': tx.jetcheckout_customer_amount,
        }
