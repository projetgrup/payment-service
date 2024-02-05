# -*- coding: utf-8 -*-
import base64
import hashlib
import logging

from odoo import _
from odoo.http import Response
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

PAGE_SIZE = 100
RESPONSE = {
    200: {"status": 0, "message": "Success"}
}

class VendorAPIService(Component):
    _inherit = "base.rest.service"
    _name = "vendor"
    _usage = "vendor"
    _collection = "payment"
    _description = """This API helps you connect vendor payment system with your specially generated key"""

    @restapi.method(
        [(["/payment/create"], "POST")],
        input_param=Datamodel("vendor.payment.create"),
        output_param=Datamodel("vendor.payment.output"),
        auth="public",
        tags=['Create Methods']
    )
    def create_payments(self, params):
        """
        Create Payments
        """
        try:
            company = self.env.company

            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            hash = self._get_hash(api, params.hash, 0)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            result = []
            vendors = self.env['res.partner'].sudo()
            for item in params.items:
                vendor = self._get_vendor(company, item.vendor)
                if not vendor:
                    vendor = self._create_vendor(company, item.vendor)
                result.append({
                    'vat': vendor.vat,
                    'link': vendor._get_payment_url(shorten=True),
                })
                vendors |= vendor

                items = []
                for payment in item.payments:
                    items.append(self._prepare_item(company, vendor, payment))
                self._create_items(items)

            types = []
            vals = {}
            

            types = []
            vals = {}
            if company.api_item_notif_mail_create_ok:
                send = False
                template = company.api_item_notif_mail_create_template
                if template:
                    if company.api_item_notif_mail_create_filter_email:
                        parent_email = parent.email
                        emails = company.api_item_notif_mail_create_filter_email.split('\n')
                        if company.api_item_notif_mail_create_filter_email_ok and any(email in parent_email for email in emails):
                            send = True
                        elif not company.api_item_notif_mail_create_filter_email_ok and all(email not in parent_email for email in emails):
                            send = True
                    else:
                        send = True
                if send:
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_email').id)
                    vals.update({'mail_template_id': template.id})
            if company.api_item_notif_sms_create_ok:
                send = False
                template = company.api_item_notif_sms_create_template
                if template:
                    if company.api_item_notif_sms_create_filter_number:
                        parent_number = parent.mobile.replace(' ', '')
                        numbers = company.api_item_notif_sms_create_filter_number.split('\n')
                        if company.api_item_notif_sms_create_filter_number_ok and any(number in parent_number for number in numbers):
                            send = True
                        elif not company.api_item_notif_sms_create_filter_number_ok and all(number not in parent_number for number in numbers):
                            send = True
                    else:
                        send = True
                if send:
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_sms').id)
                    vals.update({'sms_template_id': template.id})
            if types:
                authorized = self.env.ref('payment_jetcheckout_system.categ_authorized')
                user = self.env['res.users'].sudo().search([
                    ('company_id', '=', company.id),
                    ('partner_id.category_id', 'in', [authorized.id])
                ], limit=1) or self.env.user
                sending = self.env['payment.acquirer.jetcheckout.send'].sudo().with_context(partners=vendors).create({
                    'selection': [(6, 0, types)],
                    'type_ids': [(6, 0, types)],
                    'company_id': company.id,
                    **vals
                })
                sending.with_user(user).send()

            ResponseOk = self.env.datamodels["vendor.payment.output"]
            return ResponseOk(result=result, **RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.method(
        [(["/campaign/update"], "PUT")],
        input_param=Datamodel("vendor.campaign.update"),
        output_param=Datamodel("vendor.campaign.output"),
        auth="public",
        tags=['Update Campaigns']
    )
    def update_campaign(self, params):
        """
        Update Campaigns
        """
        try:
            company = self.env.company

            api = self._get_api(company, params.apikey)
            if not api:
                return Response("Application key is not matched", status=401, mimetype="application/json")

            hash = self._get_hash(api, params.hash, 0)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            acquirer = self._get_acquirer(company)
            for campaign in params.campaigns:
                vat, ref = None, None
                if hasattr(campaign.partner, 'vat') and campaign.partner.vat:
                    vat = campaign.partner.vat
                if hasattr(campaign.partner, 'ref') and campaign.partner.ref:
                    ref = campaign.partner.ref
                if not vat and not ref:
                    return Response("One of VAT or Reference information must be sent with campaign name", status=400, mimetype="application/json")

                vendor = self._get_vendor(company, campaign.partner)
                if not vendor:
                    if vat:
                        postfix = 'VAT %s' % vat
                    elif ref:
                        postfix = 'Reference %s' % ref
                    else:
                        postfix = 'given pairs'
                    return Response("Partner cannot be found with %s" % postfix, status=404, mimetype="application/json")

                campaign = self._get_campaign(acquirer, campaign.name)
                if not campaign:
                    return Response("Campaign name cannot be found for partner %s" % vendor.name, status=404, mimetype="application/json")

                vendor.campaign_id = campaign.id

            ResponseOk = self.env.datamodels["vendor.campaign.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.webhook(
        input_param=Datamodel("vendor.payment.item.webhook"),
        tags=['Webhook Methods']
    )
    def webhook_successful_payment(self):
        """
        Notify Successful Payment
        """
        pass

    #
    # PRIVATE METHODS
    #

    def _get_api(self, company, apikey, secretkey=False):
        domain = [('company_id', '=', company.id), ('api_key', '=', apikey)]
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

    def _get_vendor(self, company, vendor):
        domain = [('is_company', '=', True), ('company_id', '=', company.id)]
        if hasattr(vendor, 'vat') and vendor.vat:
            domain.append(('vat', '=', vendor.vat))
        if hasattr(vendor, 'ref') and vendor.ref:
            domain.append(('ref', '=', vendor.ref))
        return self.env['res.partner'].sudo().search(domain, limit=1)

    def _get_campaign(self, acquirer, campaign):
        return self.env['payment.acquirer.jetcheckout.campaign'].sudo().search([
            ('acquirer_id', '=', acquirer.id),
            ('name', '=', campaign),
        ], limit=1)

    def _create_vendor(self, company, vendor):
        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1)
        if hasattr(vendor, 'campaign') and vendor.campaign:
            campaign = acquirer.paylox_campaign_ids.filtered(lambda x: x.name == vendor.campaign)
            if len(campaign) > 1:
                campaign = campaign[0]
        else:
            campaign = acquirer.jetcheckout_campaign_id

        return self.env['res.partner'].sudo().with_context({'no_vat_validation': True, 'active_system': 'vendor'}).create({
            'is_company': True,
            'company_id': company.id,
            'campaign_id': campaign.id,
            'name': vendor.name,
            'vat': vendor.vat,
            'email': vendor.email,
            'mobile': vendor.mobile,
            'ref': getattr(vendor, 'reference', False),
        })

    def _prepare_item(self, company, vendor, payment):
        return {
            'company_id': company.id,
            'parent_id': vendor.id,
            'amount': payment.amount,
            'description': payment.description,
        }

    def _create_items(self, items):
        return self.env['payment.item'].sudo().create(items)
