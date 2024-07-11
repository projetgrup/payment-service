# -*- coding: utf-8 -*-
import base64
import hashlib
import logging

from odoo import _
from odoo.http import Response
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
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
        [(["/payment/status"], "GET")],
        input_param=Datamodel("oco.payment.read.input"),
        output_param=Datamodel("oco.payment.read.output"),
        auth="public",
        tags=['Payments']
    )
    def get_payments(self, params):
        """
        Get Payments
        """
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            company = api.company_id
            payments = self._get_payment(company, params.reference)
            if not payments:
                return Response("Payment not found", status=404, mimetype="application/json")
            
            results = [{
                "date": payment.create_date.strftime(DTF),
                "reference": payment.jetcheckout_order_id or '',
                "status": payment.state or '',
                "description": payment.state_message or '',
                "payment_payable": payment.jetcheckout_payment_amount or 0,
                "customer_rate": payment.jetcheckout_customer_rate or 0,
                "customer_amount": payment.jetcheckout_customer_amount or 0,
                "payment_paid": payment.jetcheckout_payment_paid or 0,
                "commission_rate": payment.jetcheckout_commission_rate or 0,
                "commission_amount": payment.jetcheckout_commission_amount or 0,
                "payment_net": payment.jetcheckout_payment_net or 0,
                "fund_amount": payment.jetcheckout_fund_amount or 0,
                "fund_rate": payment.jetcheckout_fund_rate or 0,
                "prepayment_amount": payment.paylox_prepayment_amount or 0,
                "installment_amount": payment.jetcheckout_installment_amount or 0,
                "installment_count": payment.jetcheckout_installment_count or 1,
                "installment_plus": payment.jetcheckout_installment_plus or 0,
                "installment_description": payment.jetcheckout_installment_description or '',
                "card_name": payment.jetcheckout_card_name or '',
                "card_number": payment.jetcheckout_card_number or '',
                "card_type": payment.jetcheckout_card_type or '',
                "card_family": payment.jetcheckout_card_family or '',
                "campaign_name": payment.jetcheckout_campaign_name or '',
                "pos_name": payment.jetcheckout_vpos_name or '',
                "transaction_id": payment.jetcheckout_transaction_id or '',
                "transaction_name": payment.reference or '',
                "partner_name": payment.partner_name or '',
                "partner_email": payment.partner_email or '',
                "partner_phone": payment.partner_phone or '',
                "partner_address": payment.partner_address or '',
                "ip_address": payment.jetcheckout_ip_address or '',
                "url_address": payment.jetcheckout_url_address or '',
            } for payment in payments]

            ResponseOk = self.env.datamodels["oco.payment.read.output"]
            return ResponseOk(payments=results, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

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
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            hash = self._get_hash(api, params.hash, 0)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            result = []
            company = api.company_id
            ocos = self.env['res.partner'].sudo()
            for item in params.items:
                oco = self._get_oco(company, item.oco)
                if not oco:
                    oco = self._create_oco(company, item.oco)
                result.append({
                    'vat': oco.vat,
                    'link': oco._get_payment_url(shorten=True),
                })
                ocos |= oco

                items = []
                for payment in item.payments:
                    items.append(self._prepare_item(company, oco, payment))
                self._create_items(items)

            types = []
            vals = {}
            

            types = []
            vals = {}
            send = True
            if company.api_item_notif_mail_create_ok:
                template = company.api_item_notif_mail_create_template
                if template:
                    if company.api_item_notif_mail_create_filter_email:
                        parent_email = parent.email
                        emails = company.api_item_notif_mail_create_filter_email.split('\n')
                        if company.api_item_notif_mail_create_filter_email_ok and all(email not in parent_email for email in emails):
                            send = False
                        elif not company.api_item_notif_mail_create_filter_email_ok and any(email in parent_email for email in emails):
                            send = False
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_email').id)
                    vals.update({'mail_template_id': template.id})
            if company.api_item_notif_sms_create_ok:
                template = company.api_item_notif_sms_create_template
                if template:
                    if company.api_item_notif_sms_create_filter_number:
                        parent_number = parent.mobile.replace(' ', '')
                        numbers = company.api_item_notif_sms_create_filter_number.split('\n')
                        if company.api_item_notif_sms_create_filter_number_ok and all(number not in parent_number for number in numbers):
                            send = False
                        elif not company.api_item_notif_sms_create_filter_number_ok and any(number in parent_number for number in numbers):
                            send = False
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_sms').id)
                    vals.update({'sms_template_id': template.id})
            if send and types:
                authorized = self.env.ref('payment_jetcheckout_system.categ_authorized')
                user = self.env['res.users'].sudo().search([
                    ('company_id', '=', company.id),
                    ('partner_id.category_id', 'in', [authorized.id])
                ], limit=1) or self.env.user
                sending = self.env['payment.acquirer.jetcheckout.send'].sudo().with_context(partners=parent).create({
                    'selection': [(6, 0, types)],
                    'type_ids': [(6, 0, types)],
                    'company_id': company.id,
                    **vals
                })
                sending.with_user(user).send()

            ResponseOk = self.env.datamodels["oco.payment.output"]
            return ResponseOk(result=result, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.method(
        [(["/campaign/update"], "PUT")],
        input_param=Datamodel("oco.campaign.update"),
        output_param=Datamodel("oco.campaign.output"),
        auth="public",
        tags=['Campaigns']
    )
    def update_campaign(self, params):
        """
        Update Campaigns
        """
        try:
            api = self._get_api(params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            hash = self._get_hash(api, params.hash, 0)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            company = api.company_id
            acquirer = self._get_acquirer(company)
            for campaign in params.campaigns:
                vat, ref = None, None
                if hasattr(campaign.partner, 'vat') and campaign.partner.vat:
                    vat = campaign.partner.vat
                if hasattr(campaign.partner, 'ref') and campaign.partner.ref:
                    ref = campaign.partner.ref
                if not vat and not ref:
                    return Response("One of VAT or Reference information must be sent with campaign name", status=400, mimetype="application/json")

                oco = self._get_oco(company, campaign.partner)
                if not oco:
                    if vat:
                        postfix = 'VAT %s' % vat
                    elif ref:
                        postfix = 'Reference %s' % ref
                    else:
                        postfix = 'given pairs'
                    return Response("Partner cannot be found with %s" % postfix, status=404, mimetype="application/json")

                campaign = self._get_campaign(acquirer, campaign.name)
                if not campaign:
                    return Response("Campaign name cannot be found for partner %s" % oco.name, status=404, mimetype="application/json")

                oco.campaign_id = campaign.id

            ResponseOk = self.env.datamodels["oco.campaign.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.webhook(
        input_param=Datamodel("oco.payment.item.webhook"),
        tags=['Payments']
    )
    def webhook_successful_payment(self):
        """
        Notify Successful Payment
        """
        pass

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
