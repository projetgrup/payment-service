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

        company = api.company_id
        if hasattr(params, 'company'):
            company = self.env['res.company'].sudo().search([('vat', '=', params.company.vat), ('parent_id', '=', company.id)])
            if not company:
                raise Exception('Company cannot be found')

        partner = api.partner_id
        if hasattr(params, 'partner'):
            partner = self.env['res.partner'].sudo().search([('vat', '=', params.partner.vat), ('company_id', '=', company.id)])
            if not partner:
                partner = self.env['res.partner'].sudo().with_context({'no_vat_validation': True, 'active_system': 'oco'}).create({
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

        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=providers, limit=1)
        values = {
            'acquirer_id': acquirer.id,
            'partner_id': partner.id,
            'amount': params.amount,
            'currency_id': company.currency_id.id,
            'company_id': company.id,
            'state': 'draft',
            'jetcheckout_api_ok': True,
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.id,
            'jetcheckout_api_method': method,
            'jetcheckout_api_order': params.order.name,
            'jetcheckout_api_card_return_url': params.url.card.result,
            'jetcheckout_api_html': getattr(params, 'html', False) or False,
            'jetcheckout_api_contact': getattr(params.partner, 'contact', False) or False,
            'jetcheckout_date_expiration': getattr(params, 'expiration', False) or False,
            'jetcheckout_campaign_name': getattr(params, 'campaign', False) or False,
            'jetcheckout_ip_address': request.httprequest.remote_addr,
        }

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
                    'name': product.name,
                    'code': product.code,
                    'qty': product.qty
                }))
            values.update({'jetcheckout_api_product_ids': product_ids})
            #values.update({'jetcheckout_api_product': ','.join(list(map(lambda x: x.name, products)))})

        if getattr(params.url, 'bank', None):
            values.update({'jetcheckout_api_bank_return_url': params.url.bank.result})
            if getattr(params.url.bank, 'webhook', None):
                values.update({'jetcheckout_api_bank_webhook_url': params.url.bank.webhook})

        tx = self.env['payment.transaction'].sudo().create(values)
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
        return self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1, raise_exception=True)














    def _get_oco(self, company, oco):
        domain = [('is_company', '=', True), ('company_id', '=', company.id)]
        if hasattr(oco, 'vat') and oco.vat:
            domain.append(('vat', '=', oco.vat))
        if hasattr(oco, 'ref') and oco.ref:
            domain.append(('ref', '=', oco.ref))
        return self.env['res.partner'].sudo().search(domain, limit=1)

    def _get_payment(self, company, reference):
        return self.env['payment.transaction'].sudo().search([
            ('company_id', '=', company.id),
            '|', ('jetcheckout_order_id', '=', reference), ('jetcheckout_transaction_id', '=', reference),
        ], limit=1)

    def _get_campaign(self, acquirer, campaign):
        return self.env['payment.acquirer.jetcheckout.campaign'].sudo().search([
            ('acquirer_id', '=', acquirer.id),
            ('name', '=', campaign),
        ], limit=1)

    def _create_oco(self, company, oco):
        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1)
        if hasattr(oco, 'campaign') and oco.campaign:
            campaign = acquirer.paylox_campaign_ids.filtered(lambda x: x.name == oco.campaign)
            if len(campaign) > 1:
                campaign = campaign[0]
        else:
            campaign = acquirer.jetcheckout_campaign_id

        return self.env['res.partner'].sudo().with_context({'no_vat_validation': True, 'active_system': 'oco'}).create({
            'is_company': True,
            'company_id': company.id,
            'campaign_id': campaign.id,
            'name': oco.name,
            'vat': oco.vat,
            'email': oco.email,
            'mobile': oco.mobile,
            'ref': getattr(oco, 'reference', False),
        })

    def _prepare_item(self, company, oco, payment):
        return {
            'company_id': company.id,
            'parent_id': oco.id,
            'amount': payment.amount,
            'description': payment.description,
        }

    def _create_items(self, items):
        return self.env['payment.item'].sudo().create(items)
