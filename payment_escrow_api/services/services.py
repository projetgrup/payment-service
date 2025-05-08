# -*- coding: utf-8 -*-
import uuid
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
from odoo.addons.payment_jetcheckout_api.services.services import auth
from odoo.exceptions import AccessError, UserError, ValidationError, MissingError

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
        <h1>Description</h1>
        <p>This API helps you create ads, payments and query their statuses with a special key which is privately generated for you. This service uses <em>Basic Authentication</em>.</p>
        <p>Firstly, use "Prepare Payment" method to initialize a payment request. Then, if everything goes well, server will send you a hash string.</p>
        <p>Now, you can navigate to <code>url</code> address to get payment form.</p>
        <p>When payment is done, its result will send to the address which you have specified when initializing the payment.</p>
        <p>Afterwards, you can use "Payment Operation" methods for cancelling, refunding, expiring or deleting the payment.</p>
    """)
    _components = {
        "securitySchemes": {
            "basicAuth": {
                "type": "http",
                "scheme": "basic",
            },
        },
        "security": {
            "basicAuth": [],
        },
        "responses": {
            "unauthorizedError": {
                "description": "Eksik veya geçersiz erişim bilgileri",
                "headers": {
                    "WWW_Authenticate": {
                        "schema": {
                            "type": "string"
                        }
                    }
                },
            },
        },
    }

    @restapi.method(
        [(["/ads/create"], "POST")],
        input_param=Datamodel("escrow.request.ads.create"),
        output_param=Datamodel("escrow.response.ads.create"),
        auth="public",
        tags=[_lt("Ad Operations")],
        name=_lt("Create Ads")
    )
    def ads_create(self, params):
        token = auth(self.env)
        ads = self._ads_create(token, params)
        return dict(ads=ads, **RESPONSE[200])

    @restapi.method(
        [(["/ads/read"], "GET")],
        input_param=Datamodel("escrow.request.ads.read"),
        output_param=Datamodel("escrow.response.ads.read"),
        auth="public",
        tags=[_lt("Ad Operations")],
        name=_lt("Read Ads")
    )
    def ads_read(self, params):
        token = auth(self.env)
        ads, page = self._ads_read(token, params)
        return dict(ads=ads, page=page, **RESPONSE[200])

    @restapi.method(
        [(["/ads/update"], "PATCH")],
        input_param=Datamodel("escrow.request.ads.update"),
        output_param=Datamodel("escrow.response.ads.update"),
        auth="public",
        tags=[_lt("Ad Operations")],
        name=_lt("Update Ads")
    )
    def ads_update(self, params):
        token = auth(self.env)
        ads = self._ads_update(token, params)
        return dict(ads=ads, **RESPONSE[200])

    @restapi.method(
        [(["/ads/delete"], "DELETE")],
        input_param=Datamodel("escrow.request.ads.delete"),
        output_param=Datamodel("escrow.response.ads.delete"),
        auth="public",
        tags=[_lt("Ad Operations")],
        name=_lt("Delete Ads")
    )
    def ads_delete(self, params):
        token = auth(self.env)
        ads = self._ads_delete(token, params)
        return dict(ads=ads, **RESPONSE[200])

    @restapi.method(
        [(["/payment/result"], "GET")],
        input_param=Datamodel("escrow.request.payment.result"),
        output_param=Datamodel("escrow.response.payment.result"),
        auth="public",
        tags=[_lt("Payment Operations")],
        name=_lt("Payment Result")
    )
    def payment_result(self, params):
        token = auth(self.env)
        result = self._payment_result(token, params)
        return dict(**result, **RESPONSE[200])

    @restapi.webhook(
        input_param=Datamodel("escrow.response.payment.webhook"),
        auth="public",
        tags=[_lt("Payment Operations")],
        name=_lt("Payment Webhook")
    )
    def payment_webhook(self):
        pass

    @restapi.method(
        [(["/payment/prepare"], "POST")],
        input_param=Datamodel("escrow.request.payment.prepare"),
        output_param=Datamodel("escrow.response.payment.prepare"),
        auth="public",
        tags=[_lt("Payment Operations")],
        name=_lt("Prepare Payment")
    )
    def payment_prepare(self, params):
        token = auth(self.env)
        tx = self._payment_prepare(token, params)
        return dict(**tx, **RESPONSE[200])

    @restapi.method(
        [(["/payment/postauth"], "PUT")],
        input_param=Datamodel("escrow.request.payment.postauth"),
        output_param=Datamodel("escrow.response.payment.postauth"),
        auth="public",
        tags=[_lt("Payment Operations")],
        name=_lt("Postauth Payment")
    )
    def payment_postauth(self, params):
        token = auth(self.env)
        tx = self._payment_postauth(token, params)
        return dict(**tx, **RESPONSE[200])

    @restapi.method(
        [(["/payment/cancel"], "PUT")],
        input_param=Datamodel("escrow.request.payment.cancel"),
        output_param=Datamodel("escrow.response.payment.cancel"),
        auth="public",
        tags=[_lt("Payment Operations")],
        name=_lt("Cancel Payment")
    )
    def payment_cancel(self, params):
        token = auth(self.env)
        tx = self._payment_cancel(token, params)
        return dict(**tx, **RESPONSE[200])

    @restapi.method(
        [(["/payment/refund"], "PUT")],
        input_param=Datamodel("escrow.request.payment.refund"),
        output_param=Datamodel("escrow.response.payment.refund"),
        auth="public",
        tags=[_lt("Payment Operations")],
        name=_lt("Refund Payment")
    )
    def payment_refund(self, params):
        token = auth(self.env)
        tx = self._payment_refund(token, params)
        return dict(**tx, **RESPONSE[200])

    @restapi.method(
        [(["/payment/expire"], "PATCH")],
        input_param=Datamodel("escrow.request.payment.expire"),
        output_param=Datamodel("escrow.response.payment.expire"),
        auth="public",
        tags=[_lt("Payment Operations")],
        name=_lt("Expire Payment")
    )
    def payment_expire(self, params):
        token = auth(self.env)
        tx = self._payment_expire(token, params)
        return dict(**tx, **RESPONSE[200])

    @restapi.method(
        [(["/payment/delete"], "DELETE")],
        input_param=Datamodel("escrow.request.payment.delete"),
        output_param=Datamodel("escrow.response.payment.delete"),
        auth="public",
        tags=[_lt("Payment Operations")],
        name=_lt("Delete Payment")
    )
    def payment_delete(self, params):
        token = auth(self.env)
        tx = self._payment_delete(token, params)
        return dict(**tx, **RESPONSE[200])

    #
    # PRIVATE METHODS
    #

    def _get_partner(self, type, company, values):
        if hasattr(values, 'country'):
            country = self.env['res.country'].sudo().search([('code', '=', values.country)], limit=1)
            if not country:
                raise MissingError(_('Country %s cannot be found') % values.country)
        else:
            country = False

        if country and hasattr(values, 'state'):
            state = self.env['res.country.state'].sudo().search([('country_id', '=', country.id), ('code', '=', values.state)], limit=1)
            if not state:
                raise MissingError(_('State %s cannot be found') % values.state)
        else:
            state = False

        partner = self.env['res.partner'].sudo().search([('vat', '=', values.vat), ('company_id', '=', company.id)], limit=1)
        if partner:
            value = {}
            if partner.name != values.name:
                value.update({'name': values.name})
            if partner.paylox_tax_office != values.taxOffice:
                value.update({'paylox_tax_office': values.taxOffice})
            if partner.email != values.email:
                value.update({'email': values.email})
            if partner.phone != values.phone:
                value.update({'phone': values.phone})
            if country and partner.country_id.id != country.id:
                value.update({'country_id': country.id})
            if state and partner.state_id.id != state.id:
                value.update({'state_id': state.id})
            if getattr(values, 'city', None) and partner.city != values.city:
                value.update({'city': values.city})
            if getattr(values, 'address', None) and partner.street != values.address:
                value.update({'street': values.address})
            if getattr(values, 'zip', None) and partner.zip != values.zip:
                value.update({'zip': values.zip})

            if type == 'owner':
                bank_values = []
                for bank in values.banks:
                    banks = self.env['res.partner.bank'].sudo().search([('partner_id', '=', partner.id)])
                    iban = sanitize_account_number(bank.iban)
                    record = fields.first(banks.filtered(lambda b: b.sanitized_acc_number == iban))
                    if record:
                        bank_value = {}
                        if record.acc_holder_name != bank.name:
                            bank_value.update({'acc_holder_name': bank.name})
                        if record.api_merchant != bank.merchant:
                            bank_value.update({'api_merchant': bank.merchant})
                        if bank_value:
                            bank_values.append((1, record.id, bank_value))
                    else:
                        bank_values.append((0, 0, {
                            'acc_number': bank.iban,
                            'acc_holder_name': bank.name,
                            'api_merchant': bank.merchant,
                        }))
                if bank_values:
                    value.update({'bank_ids': bank_values})
            if value:
                partner.write(value)

        else:
            value = {
                'name': values.name,
                'vat': values.vat,
                'paylox_tax_office': values.taxOffice,
                'email': values.email,
                'phone': values.phone,
                'country_id': country and country.id,
                'company_id': company.id,
                'system': company.system,
                'state_id': state and state.id,
                'city': getattr(values, 'city', False),
                'street': getattr(values, 'address', False),
                'zip': getattr(values, 'zip', False),
                'paylox_escrow_type': type,
            }
            if type == 'owner':
                value.update({
                    'bank_ids': [(0, 0, {
                        'acc_number': bank.iban,
                        'acc_holder_name': bank.name,
                        'api_merchant': bank.merchant,
                    }) for bank in values.banks],
                })
            partner = partner.create(value)
        return partner

    def _ads_create(self, token, params):
        values = []
        for ad in params.ads:
            owner = self._get_partner('owner', token.company_id, ad.owner)
            value = {
                'name': ad.name,
                'default_code': ad.reference,
                'description': ad.description,
                'owner_id': owner.id,
                'price': getattr(ad, 'price', 0.0),
            }
            if getattr(ad, 'images', []):
                value.update({
                    'image_1920': ad.images[0]
                })
            values.append(value)
        ads = self.env['product.product'].sudo().with_company(token.company_id).create(values)
        ads = [dict(id=ad.uid, reference=ad.default_code) for ad in ads]
        return ads

    def _ads_read_owner(self, owner):
        return {
            'name': owner.name or '',
            'vat': owner.vat or '',
            'taxOffice': owner.paylox_tax_office or '',
            'email': owner.email or '',
            'phone': owner.phone or '',
            'country': owner.country_id.name or '',
            'state': owner.state_id.name or '',
            'city': owner.city or '',
            'street': owner.street or '',
            'zip': owner.zip or '',
            'banks': [{
                'name': bank.acc_number,
                'iban': bank.acc_holder_name,
                'merchant': bank.api_merchant,
            } for bank in owner.bank_ids],
        }

    def _ads_read(self, token, params):
        domain = []
        if getattr(params, 'ads', None):
            domain.append(('uid', 'in', list(map(str, params.ads))))

        limit = params.page.size
        offset = (params.page.number - 1) * limit
        ads = self.env['product.product'].sudo() \
              .with_company(token.company_id) \
              .with_context(system=token.company_id.system) \
              .search(domain, limit=limit, offset=offset)
        ads = [
            dict(
                id=ad.uid or '',
                name=ad.name or '',
                reference=ad.default_code or '',
                description=ad.description or '',
                owner=self._ads_read_owner(ad.owner_id),
                price=ad.price or 0.0,
                images=[base64.b64encode(ad.image_1920)] if ad.image_1920 else [],
            ) for ad in ads
        ]
        page = dict(
            size=params.page.size,
            number=params.page.number,
            count=len(ads),
        )
        return ads, page

    def _ads_update(self, token, params):
        ads = []
        for ad in params.ads:
            _ad = self.env['product.product'].sudo() \
                 .with_company(token.company_id) \
                 .with_context(system=token.company_id.system) \
                 .search([('uid', '=', str(ad.id))], limit=1)
            if not _ad:
                raise MissingError(_('Ad %s cannot be found') % str(ad.id))

            values = {}
            if getattr(ad, 'name', None) and _ad.name != ad.name:
                values.update({'name': ad.name})
            if getattr(ad, 'reference', None) and _ad.default_code != ad.reference:
                values.update({'default_code': ad.reference})
            if getattr(ad, 'description', None) and _ad.description != ad.description:
                values.update({'description': ad.description})
            if hasattr(ad, 'price'):
                values.update({'price': ad.price or 0.0})
            if hasattr(ad, 'images'):
                values.update({'image_1920': ad.images and ad.images[0] or False})
            if getattr(ad, 'owner', None):
                values_owner = {}
                if _ad.owner_id.paylox_escrow_type != 'owner':
                    values_owner.update({'paylox_escrow_type': 'owner'})
                if getattr(ad.owner, 'name', None) and _ad.owner_id.name != ad.owner.name:
                    values_owner.update({'name': ad.owner.name})
                if getattr(ad.owner, 'vat', None) and _ad.owner_id.vat != ad.owner.vat:
                    values_owner.update({'vat': ad.owner.vat})
                if getattr(ad.owner, 'taxOffice', None) and _ad.owner_id.paylox_tax_office != ad.owner.taxOffice:
                    values_owner.update({'paylox_tax_office': ad.taxOffice})
                if getattr(ad.owner, 'email', None) and _ad.owner_id.email != ad.owner.email:
                    values_owner.update({'email': ad.owner.email})
                if getattr(ad.owner, 'phone', None) and _ad.owner_id.phone != ad.owner.phone:
                    values_owner.update({'phone': ad.owner.phone})
                if hasattr(ad.owner, 'country') and _ad.owner_id.country_id.code != ad.owner.country:
                    country = self.env['res.country'].sudo().search([('code', '=', ad.owner.country)], limit=1)
                    if not country:
                        raise MissingError(_('Country %s cannot be found') % ad.owner.country)
                    values_owner.update({'country_id': country.id})
                if hasattr(ad.owner, 'state') and _ad.owner_id.state_id.code != ad.owner.state:
                    state = self.env['res.country.state'].sudo().search([('country_id', '=', values_owner.get('country_id', _ad.owner_id.country_id.code)), ('code', '=', ad.owner.state)], limit=1)
                    if not state:
                        raise MissingError(_('State %s cannot be found') % ad.owner.country)
                    values_owner.update({'state_id': state.id})
                if hasattr(ad.owner, 'city') and _ad.owner_id.city != ad.owner.city:
                    values_owner.update({'city': ad.owner.city or False})
                if hasattr(ad.owner, 'address') and _ad.owner_id.street != ad.owner.address:
                    values_owner.update({'street': ad.owner.address or False})
                if hasattr(ad.owner, 'zip') and _ad.owner_id.zip != ad.owner.zip:
                    values_owner.update({'zip': ad.owner.zip or False})
                if hasattr(ad.owner, 'banks'):
                    values_banks = []
                    for bank in ad.owner.banks:
                        banks = self.env['res.partner.bank'].sudo().search([('partner_id', '=', _ad.owner_id.id)])
                        iban = sanitize_account_number(bank.iban)
                        _bank = fields.first(banks.filtered(lambda b: b.sanitized_acc_number == iban))
                        if _bank:
                            value_bank = {}
                            if getattr(bank, 'name', None) and _bank.acc_holder_name != bank.name:
                                value_bank.update({'acc_holder_name': bank.name})
                            if getattr(bank, 'merchant', None) and _bank.api_merchant != bank.merchant:
                                value_bank.update({'api_merchant': bank.merchant})
                            if value_bank:
                                values_banks.append((1, _bank.id, value_bank))
                        else:
                            values_banks.append((0, 0, {
                                'acc_number': bank.iban,
                                'acc_holder_name': bank.name,
                                'api_merchant': bank.merchant,
                            }))
                    if values_banks:
                        values_owner.update({'bank_ids': values_banks})
                if values_owner:
                    _ad.owner_id.write(values_owner)
            if values:
                _ad.write(values)
            ads.append(dict(id=_ad.uid, reference=_ad.default_code))
        return ads

    def _ads_delete(self, token, params):
        _ads = self.env['product.product'].sudo() \
              .with_company(token.company_id) \
              .with_context(system=token.company_id.system) \
              .search([('uid', 'in', list(map(str, params.ads)))])
        if not _ads:
            raise MissingError(_('No ads found'))

        ads = [dict(id=ad.uid, reference=ad.default_code) for ad in _ads]
        _ads.unlink()
        return ads

    def _payment_prepare(self, token, params):
        amount = 0
        ads = []
        for ad in params.ads:
            _ad = self.env['product.product'].sudo() \
                  .with_company(token.company_id) \
                  .with_context(system=token.company_id.system) \
                  .search([('uid', '=', str(ad.id))], limit=1)
            if not _ad:
                raise MissingError(_('Ad %s cannot be found') % str(ad.id))
            price = getattr(ad, 'price', _ad.price)
            ads.append((0, 0, {
                'product_id': _ad.id,
                'price': price,
                'qty': 1,
            }))
            amount += price

        uid = str(uuid.uuid4())
        company = token.company_id
        customer = self._get_partner('customer', token.company_id, params.customer)
        hash = base64.b64encode(hashlib.sha256(''.join([uid, params.reference]).encode('utf-8')).digest()).decode('utf-8')
        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1)
        value = {
            'state': 'draft',
            'company_id': company.id,
            'partner_id': customer.id,
            'acquirer_id': acquirer.id,
            'currency_id': company.currency_id.id,
            'jetcheckout_payment_type': 'virtual_pos',
            'jetcheckout_order_id': uid,
            'jetcheckout_api_ok': True,
            'jetcheckout_api_hash': hash,
            'jetcheckout_api_id': params.reference,
            'jetcheckout_api_method': 'card',
            'jetcheckout_api_card_redirect_url': params.redirectUrl,
            'jetcheckout_api_card_result_url': 'https://%s/payment/card/result' % request.httprequest.host,
            'paylox_product_ids': ads,
            'amount': amount,
        }
        if hasattr(params, 'amount'):
            value.update({'amount': params.amount})
        if hasattr(params, 'preauth'):
            value.update({'jetcheckout_preauth': params.preauth})
        tx = self.env['payment.transaction'].sudo().create(value)
        return dict(id=uid, url='https://%s/tx/%s' % (request.httprequest.host, tx.jetcheckout_order_id))

    def _payment_postauth(self, token, params):
        tx = request.env['payment.transaction'].sudo().paylox_get_transaction(str(params.id))
        if not tx:
            raise MissingError(_('Transaction cannot be found'))

        tx.with_context(amount=params.amount)._send_capture_request()
        return dict()

    def _payment_result(self, token, params):
        tx = request.env['payment.transaction'].sudo().paylox_get_transaction(str(params.id))
        if not tx:
            raise MissingError(_('Transaction cannot be found'))
    
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
