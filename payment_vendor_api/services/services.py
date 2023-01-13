# -*- coding: utf-8 -*-
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
        [(["/item/create"], "POST")],
        input_param=Datamodel("vendor.item.input"),
        output_param=Datamodel("vendor.item.output"),
        auth="public",
        tags=['Create Methods']
    )
    def create_item(self, params):
        """
        Create Payment Item
        """
        try:
            company = self.env.company
            key = self._auth(company.id, params.application_key, params.secret_key)
            if not key:
                return Response("Application key and secret key are not matched", status=401, mimetype="application/json")

            school = self.env['res.student.school'].sudo().search([('company_id', '=', company.id), ('code', '=', params.school_code)], limit=1)
            if not school:
                return Response("No school found with given code", status=404, mimetype="application/json")

            bursary = self.env['res.student.bursary'].sudo()
            if hasattr(params, 'bursary_code') and params.bursary_code:
                bursary = bursary.search([('company_id', '=', company.id), ('code', '=', params.bursary_code)], limit=1)

            classroom = self.env['res.student.class'].sudo().search([('company_id', '=', company.id), ('code', '=', params.class_code)], limit=1)
            if not classroom:
                return Response("No classrocreate_stom found with given code", status=404, mimetype="application/json")

            categ_api = self.env.ref('payment_jetcheckout_api.categ_api')
            parent = self.env['res.partner'].sudo().search([('company_id', '=', company.id), ('email', '=', params.parent_email)], limit=1)
            if not parent:
                parent = self.env['res.partner'].sudo().create({
                    'name': params.parent_name,
                    'email': params.parent_email,
                    'mobile': params.parent_mobile,
                    'is_company': True,
                    'parent_id': False,
                    'company_id': company.id,
                    'category_id': [(6, 0, categ_api.ids)],
                })

            if not params.ref:
                return Response("No ref found with given code", status=404, mimetype="application/json")

            students = self.env['res.partner'].with_context({'no_vat_validation': True, 'active_system': 'student'}).sudo()
            student = students.search([('company_id', '=', company.id), ('ref', '=', params.ref)])
            if len(student) > 1:
                return Response("There is more than one student with the same characteristics in the records. Please contact the system administrator.", status=400, mimetype="application/json")

            vals = {
                'name': params.name,
                'vat': params.vat,
                'school_id': school.id,
                'bursary_id': bursary.id,
                'ref': params.ref,
                'class_id': classroom.id,
                'parent_id': parent.id,
                'is_company': False,
                'company_id': company.id,
                'category_id': [(6, 0, categ_api.ids)],
            }
            if student:
                student.write(vals)
            else:
                student = students.create(vals)

            authorized = self.env.ref('payment_jetcheckout_system.categ_authorized')
            user = self.env['res.users'].sudo().search([('company_id', '=', company.id), ('partner_id.category_id', 'in', [authorized.id])], limit=1) or self.env.user
            type_email = self.env.ref('payment_jetcheckout_system.send_type_email')
            type_sms = self.env.ref('payment_jetcheckout_system.send_type_sms')
            mail_template = self.env['mail.template'].sudo().search([('company_id', '=',company.id)], limit=1)
            sms_template = self.env['sms.template'].sudo().search([('company_id', '=', company.id)], limit=1)
            sending = self.env['payment.acquirer.jetcheckout.send'].sudo().with_context(partners=parent).create({
                'selection': [(6, 0, type_email.ids + type_sms.ids)],
                'type_ids': [(6, 0, type_email.ids + type_sms.ids)],
                'mail_template_id': mail_template.id,
                'sms_template_id': sms_template.id,
                'company_id': company.id,
            })
            sending.with_user(user).send()

            ResponseOk = self.env.datamodels["vendor.item.output"]
            return ResponseOk(**RESPONSE[200])
        except Exception as e:
            _logger.error(e)
            return Response("Server Error", status=500, mimetype="application/json")

    @restapi.webhook(
        input_param=Datamodel("vendor.webhook"),
        tags=['Webhook Methods']
    )
    def webhook_successful_payment(self):
        """
        Notify Successful Payment
        """
        pass

    # PRIVATE METHODS
    def _auth(self, _company, _apikey, _secretkey=False):
        domain = [('company_id', '=', _company), ('api_key', '=', _apikey)]
        if _secretkey:
            domain.append(('secret_key', '=', _secretkey))
        return self.env["payment.acquirer.jetcheckout.api"].sudo().search(domain, limit=1)
