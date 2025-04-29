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

class SupplierAPIService(Component):
    _inherit = "base.rest.service"
    _name = "supplier"
    _usage = "supplier"
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
        [(["/prepare"], "POST")],
        input_param=Datamodel("supplier.payment.prepare.input"),
        output_param=Datamodel("supplier.payment.prepare.output"),
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

            self._create_transaction(api, hash, params)

            tx = self._create_transaction(api, hash, params)
            id = tx.jetcheckout_order_id
            url = 'https://%s/payment?=%s' % (request.httprequest.host, quote(hash))
            ResponseOk = self.env.datamodels["supplier.payment.prepare.output"]
            return ResponseOk(id=id, url=url, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")
    payment_prepare.__doc__ = _lt("Prepare Payment")

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

        if hasattr(params.supplier, 'country'):
            country = self.env['res.country'].sudo().search([('code', '=', params.supplier.country)], limit=1)
        else:
            country = False

        if country and hasattr(params.supplier, 'state'):
            state = self.env['res.country.state'].sudo().search([('country_id', '=', country.id), ('code', '=', params.supplier.state)], limit=1)
        else:
            state = False

        supplier = self.env['res.partner'].sudo().search([('vat', '=', params.supplier.vat), ('company_id', '=', company.id)], limit=1)
        if supplier:
            values = {}
            if supplier.name != params.supplier.name:
                values.update({'name': params.supplier.name})
            if supplier.email != params.supplier.email:
                values.update({'email': params.supplier.email})
            if supplier.phone != params.supplier.phone:
                values.update({'phone': params.supplier.phone})
            if country and supplier.country_id.id != country.id:
                values.update({'country_id': country.id})
            if state and supplier.state_id.id != state.id:
                values.update({'state_id': state.id})
            if getattr(params.supplier, 'city', None) and supplier.city != params.supplier.city:
                values.update({'city': params.supplier.city})
            if getattr(params.supplier, 'address', None) and supplier.street != params.supplier.address:
                values.update({'street': params.supplier.address})
            if getattr(params.supplier, 'zip', None) and supplier.zip != params.supplier.zip:
                values.update({'zip': params.supplier.zip})

            banks_values = []
            for bank in params.supplier.banks:
                banks = self.env['res.partner.bank'].sudo().search([('partner_id', '=', supplier.id)])
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
                supplier.write(values)

        else:
            supplier = supplier.create({
                'name': params.supplier.name,
                'vat': params.supplier.vat,
                'email': params.supplier.email,
                'phone': params.supplier.phone,
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
                }) for bank in params.supplier.banks],
            })

        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1)
        values = {
            'state': 'draft',
            'amount': getattr(params, 'amount', 0.0),
            'company_id': company.id,
            'acquirer_id': acquirer.id,
            'partner_id': supplier.id,
            'currency_id': company.currency_id.id,
            'jetcheckout_payment_type': 'virtual_pos',
            'jetcheckout_api_ok': True,
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.id,
            'jetcheckout_api_method': 'card',
        }

        tx = self.env['payment.transaction'].sudo().create(values)
        tx.write({
            'partner_name': params.supplier.name,
            'partner_vat': params.supplier.vat,
            'partner_email': params.supplier.email,
            'partner_address': params.supplier.address,
            'partner_phone': params.supplier.phone,
            'partner_zip': getattr(params.supplier, 'zip', '') or '',
            'partner_city': getattr(params.supplier, 'city', '') or '',
            'partner_country_id': country and country.id or False,
            'partner_state_id': state and state.id or False,
        })
        return tx
