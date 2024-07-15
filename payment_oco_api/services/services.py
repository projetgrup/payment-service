# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
from urllib.parse import quote

from odoo.http import Response, request
from odoo.tools.translate import _, _lt
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
        input_param=Datamodel("oco.payment.create"),
        output_param=Datamodel("oco.payment.output"),
        auth="public",
        tags=['Payments']
    )
    def create_payments(self, params):
        """
        Create Payments
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
            return ResponseOk(hash=quote(hash), **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response(str(e), status=500, mimetype="application/json")

    create_payments.__doc__ = _lt("Prepare Payment")

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

        company = api.company_id
        if hasattr(params, 'company'):
            company = self.env['res.company'].sudo().search([('vat', '=', params.company.vat), ('parent_id', '=', company.id)])
            if not company:
                raise Exception('Company cannot be found')

        partner = api.partner_id
        if hasattr(params, 'partner'):
            partner = self.env['res.partner'].sudo().search([('vat', '=', params.partner.vat), ('company_id', '=', company.id)]).with_company(company)
            if not partner:
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
                    'zip': getattr(params.partner, 'zip', '') or '',
                    'city': getattr(params.partner, 'city', '') or '',
                })

        acquirer = self._get_acquirer(company=company)
        values = {
            'acquirer_id': acquirer.id,
            'partner_id': partner.id,
            'amount': params.order.amount,
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
        }

        products = getattr(params.order, 'products', [])
        if products:
            product_ids = []
            prods = self.env['product.product'].sudo().with_context(system='oco')
            for product in products:
                prod = prods.search([
                    #('type', '=', 'product'),
                    ('type', '=', 'consu'),
                    ('default_code', '=', product),
                    ('company_id', '=', api.company_id.id)
                ])
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
                    'qty': product.qty
                }))
            values.update({'jetcheckout_api_product_ids': product_ids})
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

    def _get_acquirer(self, company):
        return self.env['payment.acquirer'].sudo().with_company(company)._get_acquirer(company=company, providers=['jetcheckout'], limit=1, raise_exception=True)
