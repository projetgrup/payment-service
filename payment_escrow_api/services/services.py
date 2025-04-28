# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
from urllib.parse import quote

from odoo import fields, _, _lt
from odoo.http import request, Response
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.addons.component.core import Component
from odoo.addons.base.models.res_bank import sanitize_account_number

_logger = logging.getLogger(__name__)

PAGE_SIZE = 100
RESPONSE = {
    200: {"status": 0, "message": "Success"}
}

class EscrowAPIService(Component):
    _inherit = "base.rest.service"
    _name = "escrow"
    _usage = "escrow"
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
        [(["/ads/create"], "POST")],
        input_param=Datamodel("escrow.request.ads.create"),
        output_param=Datamodel("escrow.response.ads.create"),
        auth="public",
        tags=[_lt("Ad Operations")]
    )
    def ads_create(self, params):
        pass
    ads_create.__doc__ = _lt("Create Ads")

    @restapi.method(
        [(["/ads/get"], "GET")],
        input_param=Datamodel("escrow.request.ads.get"),
        output_param=Datamodel("escrow.response.ads.get"),
        auth="public",
        tags=[_lt("Ad Operations")]
    )
    def ads_get(self, params):
        pass
    ads_get.__doc__ = _lt("List Ads")

    @restapi.method(
        [(["/ads/update"], "PATCH")],
        input_param=Datamodel("escrow.request.ads.update"),
        output_param=Datamodel("escrow.response.ads.update"),
        auth="public",
        tags=[_lt("Ad Operations")]
    )
    def ad_patch(self, params):
        pass
    ad_patch.__doc__ = _lt("Update Ads")

    @restapi.method(
        [(["/ads/delete"], "DELETE")],
        input_param=Datamodel("escrow.request.ads.delete"),
        output_param=Datamodel("escrow.response.ads.delete"),
        auth="public",
        tags=[_lt("Ad Operations")]
    )
    def ad_delete(self, params):
        pass
    ad_delete.__doc__ = _lt("Delete Ads")

    @restapi.method(
        [(["/payment/result"], "GET")],
        input_param=Datamodel("escrow.request.payment.result"),
        output_param=Datamodel("escrow.response.payment.result"),
        auth="public",
        tags=[_lt("Payment Operations")]
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
        input_param=Datamodel("escrow.response.payment.webhook"),
        auth="public",
        tags=[_lt("Payment Operations")]
    )
    def payment_webhook(self):
        pass
    payment_webhook.__doc__ = _lt("Payment Webhook")

    @restapi.method(
        [(["/payment/prepare"], "POST")],
        input_param=Datamodel("escrow.request.payment.prepare"),
        output_param=Datamodel("escrow.response.payment.prepare"),
        auth="public",
        tags=[_lt("Payment Operations")]
    )
    def payment_prepare(self, params):
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            hash = self._get_hash(api, params.hash, params.id)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            self._create_transaction(api, hash, params)

            tx = self._create_transaction(api, hash, params)
            id = tx.jetcheckout_order_id
            url = 'https://%s/payment?=%s' % (request.httprequest.host, quote(hash))
            ResponseOk = self.env.datamodels["escrow.payment.prepare.output"]
            return ResponseOk(id=id, url=url, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_prepare.__doc__ = _lt("Prepare Payment")

    @restapi.method(
        [(["/payment/cancel"], "PUT")],
        input_param=Datamodel("escrow.request.payment.cancel"),
        output_param=Datamodel("escrow.response.payment.cancel"),
        auth="public",
        tags=[_lt("Payment Operations")]
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
        [(["/payment/refund"], "PUT")],
        input_param=Datamodel("escrow.request.payment.refund"),
        output_param=Datamodel("escrow.response.payment.refund"),
        auth="public",
        tags=[_lt("Payment Operations")]
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
        [(["/payment/expire"], "PATCH")],
        input_param=Datamodel("escrow.request.payment.expire"),
        output_param=Datamodel("escrow.response.payment.expire"),
        auth="public",
        tags=[_lt("Payment Operations")]
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
        [(["/payment/delete"], "DELETE")],
        input_param=Datamodel("escrow.request.payment.delete"),
        output_param=Datamodel("escrow.response.payment.delete"),
        auth="public",
        tags=[_lt("Payment Operations")]
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

    def _create_transaction(self, api, hash, params):
        company = api.company_id

        if hasattr(params.escrow, 'country'):
            country = self.env['res.country'].sudo().search([('code', '=', params.escrow.country)], limit=1)
        else:
            country = False

        if country and hasattr(params.escrow, 'state'):
            state = self.env['res.country.state'].sudo().search([('country_id', '=', country.id), ('code', '=', params.escrow.state)], limit=1)
        else:
            state = False

        escrow = self.env['res.partner'].sudo().search([('vat', '=', params.escrow.vat), ('company_id', '=', company.id)], limit=1)
        if escrow:
            values = {}
            if escrow.name != params.escrow.name:
                values.update({'name': params.escrow.name})
            if escrow.email != params.escrow.email:
                values.update({'email': params.escrow.email})
            if escrow.phone != params.escrow.phone:
                values.update({'phone': params.escrow.phone})
            if country and escrow.country_id.id != country.id:
                values.update({'country_id': country.id})
            if state and escrow.state_id.id != state.id:
                values.update({'state_id': state.id})
            if getattr(params.escrow, 'city', None) and escrow.city != params.escrow.city:
                values.update({'city': params.escrow.city})
            if getattr(params.escrow, 'address', None) and escrow.street != params.escrow.address:
                values.update({'street': params.escrow.address})
            if getattr(params.escrow, 'zip', None) and escrow.zip != params.escrow.zip:
                values.update({'zip': params.escrow.zip})

            banks_values = []
            for bank in params.escrow.banks:
                banks = self.env['res.partner.bank'].sudo().search([('partner_id', '=', escrow.id)])
                iban = sanitize_account_number(bank.iban)
                record = fields.first(banks.filtered(lambda b: b.sanitized_acc_number == iban))
                if record:
                    bank_values = {}
                    if record.acc_holder_name != bank.name:
                        bank_values.update({'acc_holder_name': bank.name})
                    if record.api_merchant != bank.merchant:
                        bank_values.update({'api_merchant': bank.merchant})
                    if bank_values:
                        banks_values.append((1, record.id, bank_values))
                else:
                    banks_values.append((0, 0, {
                        'acc_number': bank.iban,
                        'acc_holder_name': bank.name,
                        'api_merchant': bank.merchant,
                    }))
            if banks_values:
                values.update({'bank_ids': banks_values})
            if values:
                escrow.write(values)

        else:
            escrow = escrow.create({
                'name': params.escrow.name,
                'vat': params.escrow.vat,
                'email': params.escrow.email,
                'phone': params.escrow.phone,
                'country_id': country and country.id,
                'company_id': company.id,
                'system': company.system,
                'state_id': state and state.id,
                'city': getattr(params, 'city', False),
                'street': getattr(params, 'address', False),
                'zip': getattr(params, 'zip', False),
                'bank_ids': [(0, 0, {
                    'acc_number': bank.iban,
                    'acc_holder_name': bank.name,
                    'api_merchant': bank.merchant,
                }) for bank in params.escrow.banks],
            })

        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1)
        values = {
            'state': 'draft',
            'amount': getattr(params, 'amount', 0.0),
            'company_id': company.id,
            'acquirer_id': acquirer.id,
            'partner_id': escrow.id,
            'currency_id': company.currency_id.id,
            'jetcheckout_payment_type': 'virtual_pos',
            'jetcheckout_api_ok': True,
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.id,
            'jetcheckout_api_method': 'card',
        }

        tx = self.env['payment.transaction'].sudo().create(values)
        tx.write({
            'partner_name': params.escrow.name,
            'partner_vat': params.escrow.vat,
            'partner_email': params.escrow.email,
            'partner_address': params.escrow.address,
            'partner_phone': params.escrow.phone,
            'partner_zip': getattr(params.escrow, 'zip', '') or '',
            'partner_city': getattr(params.escrow, 'city', '') or '',
            'partner_country_id': country and country.id or False,
            'partner_state_id': state and state.id or False,
        })
        return tx
