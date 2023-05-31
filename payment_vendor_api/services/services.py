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

            hash = self._get_hash(api, params.hash, 1)
            if not hash:
                return Response("Hash is not matched", status=401, mimetype="application/json")

            vendors = self.env['res.partner'].sudo()
            for item in params.items:
                vendor = self._get_vendor(company, item.vendor)
                if not vendor:
                    vendor = self._create_vendor(company, item.vendor)
                vendors |= vendor

                items = []
                for payment in item.payments:
                    items.append(self._prepare_item(company, vendor, payment))
                self._create_items(items)

            types = []
            vals = {}
            if company.api_item_notif_mail_create_ok:
                template = company.api_item_notif_mail_create_template
                if template:
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_email').id)
                    vals.update({'mail_template_id': template.id})
            if company.api_item_notif_sms_create_ok:
                template = company.api_item_notif_sms_create_template
                if template:
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
        domain = [('company_id', '=', company), ('api_key', '=', apikey)]
        if secretkey:
            domain.append(('secret_key', '=', secretkey))
        return self.env['payment.acquirer.jetcheckout.api'].sudo().search(domain, limit=1)

    def _get_hash(self, key, hash, id):
        hashed = base64.b64encode(hashlib.sha256(''.join([key.api_key, key.secret_key, str(id)]).encode('utf-8')).digest()).decode('utf-8')
        if hashed != hash:
            return False
        return hash

    def _get_vendor(self, company, vendor):
        return self.env['res.partner'].sudo().search([
            ('is_company', '=', True),
            ('company_id', '=', company.id),
            ('vat', '=', vendor.vat)
        ], limit=1)

    def _create_vendor(self, company, vendor):
        acquirer = self.env['payment.acquirer']._get_acquirer(company=company, providers=['jetcheckout'], limit=1)
        if hasattr(vendor, 'campaign') and vendor.campaign:
            campaign = acquirer.jetcheckout_campaign_ids.filtered(lambda x: x.name == vendor.campaign)
            if len(campaign) > 1:
                campaign = campaign[0]
        else:
            campaign = acquirer.jetcheckout_campaign_id
 
        return self.env['res.partner'].sudo().with_context({'no_vat_validation': True, 'active_system': 'vendor'}).create({
            'is_company': True,
            'company_id': company.id,
            'name': vendor.name,
            'vat': vendor.vat,
            'ref': vendor.ref,
            'email': vendor.email,
            'mobile': vendor.mobile,
            'campaign_id': campaign.id,
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
