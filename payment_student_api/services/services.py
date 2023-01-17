# -*- coding: utf-8 -*-
from odoo.http import Response
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component
from odoo import _

PAGESIZE = 100
RESPONSE = {
    200: {"response_code": 0, "response_message": "Success"}
}


class StudentAPIService(Component):
    _inherit = "base.rest.service"
    _name = "student"
    _usage = "student"
    _collection = "payment"
    _description = """This API helps you connect student payment system with your specially generated key"""

    @restapi.method(
        [(["/schools"], "GET")],
        input_param=Datamodel("student.school.input"),
        output_param=Datamodel("student.school.output"),
        auth="public",
        tags=['List Methods']
    )
    def list_school(self, params):
        """
        List Schools
        """
        SchoolResponse = self.env.datamodels["student.school.output"]
        company = self.env.company.id
        key = self._auth(company, params.application_key)
        if not key:
            return Response("Application key is not matched", status=401, mimetype="application/json")

        page = params.page - 1
        if page < 0:
            return Response("Page number cannot be lower than 1", status=400, mimetype="application/json")

        domain = [("company_id", "=", company)]
        if hasattr(params, 'name') and params.name:
            domain.append(("name", "ilike", params.name))
        if hasattr(params, 'code') and  params.code:
            domain.append(("code", "ilike", params.code))

        schools = []
        for i in self.env["res.student.school"].sudo().search(domain, offset=PAGESIZE * page, limit=100):
            schools.append(dict(id=i.id, name=i.name, code=i.code))
        if not schools:
            return Response("No records found", status=404, mimetype="application/json")
        return SchoolResponse(schools=schools, **RESPONSE[200])

    @restapi.method(
        [(["/classes"], "GET")],
        input_param=Datamodel("student.class.input"),
        output_param=Datamodel("student.class.output"),
        auth="public",
        tags=['List Methods']
    )
    def list_class(self, params):
        """
        List Classes
        """
        ClassResponse = self.env.datamodels["student.class.output"]
        company = self.env.company.id
        key = self._auth(company, params.application_key)
        if not key:
            return Response("Application key is not matched", status=401, mimetype="application/json")

        page = params.page - 1
        if page < 0:
            return Response("Page number cannot be lower than 1", status=400, mimetype="application/json")

        domain = [("company_id", "=", company)]
        if hasattr(params, 'name') and params.name:
            domain.append(("name", "ilike", params.name))
        if hasattr(params, 'code') and  params.code:
            domain.append(("code", "ilike", params.code))

        classes = []
        for i in self.env["res.student.class"].sudo().search(domain, offset=PAGESIZE * page, limit=100):
            classes.append(dict(id=i.id, name=i.name, code=i.code))
        if not classes:
            return Response("No records found", status=404, mimetype="application/json")
        return ClassResponse(classes=classes, **RESPONSE[200])

    @restapi.method(
        [(["/bursaries"], "GET")],
        input_param=Datamodel("student.bursary.input"),
        output_param=Datamodel("student.bursary.output"),
        auth="public",
        tags=['List Methods']
    )
    def list_bursary(self, params):
        """
        List Bursaries
        """
        BursaryResponse = self.env.datamodels["student.bursary.output"]
        company = self.env.company.id
        key = self._auth(company, params.application_key)
        if not key:
            return Response("Application key is not matched", status=401, mimetype="application/json")

        page = params.page - 1
        if page < 0:
            return Response("Page number cannot be lower than 1", status=400, mimetype="application/json")

        domain = [("company_id", "=", company)]
        if hasattr(params, 'name') and params.name:
            domain.append(("name", "ilike", params.name))
        if hasattr(params, 'code') and  params.code:
            domain.append(("code", "ilike", params.code))

        bursaries = []
        for i in self.env["res.student.bursary"].sudo().search(domain, offset=PAGESIZE * page, limit=100):
            bursaries.append(dict(id=i.id, name=i.name, code=i.code))
        if not bursaries:
            return Response("No records found", status=404, mimetype="application/json")
        return BursaryResponse(bursaries=bursaries, **RESPONSE[200])

    @restapi.method(
        [(["/students"], "GET")],
        input_param=Datamodel("student.child.input"),
        output_param=Datamodel("student.child.output"),
        auth="public",
        tags=['List Methods']
    )
    def list_student(self, params):
        """
        List Students And Parents
        """
        StudentResponse = self.env.datamodels["student.child.output"]
        company = self.env.company.id
        key = self._auth(company, params.application_key)
        if not key:
            return Response("Application key is not matched", status=401, mimetype="application/json")

        page = params.page - 1
        if page < 0:
            return Response("Page number cannot be lower than 1", status=400, mimetype="application/json")

        domain = [("company_id", "=", company), ("system", "=", "student"), ("parent_id", "!=", False),
                  ("is_company", "=", False)]
        if hasattr(params, 'name') and params.name:
            domain.append(("name", "ilike", params.name))
        if hasattr(params, 'code') and  params.code:
            domain.append(("code", "ilike", params.vat))

        students = []
        for i in self.env["res.partner"].sudo().search(domain, offset=PAGESIZE * page, limit=100):
            students.append(dict(id=i.id, name=i.name, vat=i.vat, parent=i.parent_id.name))
        if not students:
            return Response("No records found", status=404, mimetype="application/json")
        return StudentResponse(students=students, **RESPONSE[200])

    @restapi.method(
        [(["/payments"], "GET")],
        input_param=Datamodel("student.payment.input"),
        output_param=Datamodel("student.payment.output"),
        auth="public",
        tags=['List Methods']
    )
    def list_payment(self, params):
        """
        List Payments
        """
        PaymentResponse = self.env.datamodels["student.payment.output"]
        company = self.env.company.id
        key = self._auth(company, params.application_key)
        if not key:
            return Response("Application key is not matched", status=401, mimetype="application/json")

        page = params.page - 1
        if page < 0:
            return Response("Page number cannot be lower than 1", status=400, mimetype="application/json")

        payments = []
        domain = [("company_id", "=", company), ("partner_id.email", "=", params.email)]
        for i in self.env["payment.transaction"].sudo().search(domain, offset=PAGESIZE * page, limit=100):
            payments.append(dict(id=i.id, date=i.create_date.strftime("%d-%m-%Y"), amount=i.amount, state=i.state))
        if not payments:
            return Response("No records found", status=404, mimetype="application/json")
        return PaymentResponse(payments=payments, **RESPONSE[200])

    @restapi.method(
        [(["/create"], "POST")],
        input_param=Datamodel("student.child.create"),
        output_param=Datamodel("student.child.output"),
        auth="public",
        tags=['Create Methods']
    )
    def create_student(self, params):
        """
        Create Student
        """
        StudentResponse = self.env.datamodels["student.child.output"]
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

        values = {
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
            student.write(values)
        else:
            student = students.create(values)

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
            sending = self.env['payment.acquirer.jetcheckout.send'].sudo().with_context(partners=parent).create({
                'selection': [(6, 0, types)],
                'type_ids': [(6, 0, types)],
                'company_id': company.id,
                **vals
            })
            sending.with_user(user).send()

        students = [dict(id=student.id, name=student.name, vat=student.vat, parent=student.parent_id.name)]
        return StudentResponse(students=students, **RESPONSE[200])

    @restapi.method(
        [(["/delete"], "DELETE")],
        input_param=Datamodel("student.child.delete"),
        auth="public",
        tags=['Delete Methods']
    )
    def delete_student(self, params):
        """
        Delete Student
        """
        company = self.env.company.id
        key = self._auth(company, params.application_key, params.secret_key)
        if not key:
            return Response("Application key and secret key are not matched", status=401, mimetype="application/json")

        if hasattr(params, 'vat') and params.vat:
            student = self.env['res.partner'].sudo().search([('company_id', '=', company), ('parent_id', '!=', False), ('vat', '=ilike', '%%%s' % params.vat)], limit=1)
        elif hasattr(params, 'ref') and params.ref:
            student = self.env['res.partner'].sudo().search([('company_id', '=', company), ('parent_id', '!=', False), ('ref', '=', params.ref)], limit=1)
        else:
            return Response("Student citizen number or reference number must be provided", status=400, mimetype="application/json")

        if not student:
            return Response("No student found with given parameters", status=404, mimetype="application/json")
        if self.env['payment.item'].sudo().search_count([('company_id', '=', company), ('child_id', '=', student.id), ('paid', '=', True)]):
            return Response("Student who has paid items cannot be deleted", status=400, mimetype="application/json")

        student.write({'active': False})
        student.message_post(body=_('Student has been archieved from API'))
        if not self.env['res.partner'].sudo().search_count([('company_id', '=', company), ('parent_id', '=', student.parent_id.id), ('active', '=', True)]):
            student.parent_id.write({'active': False})
            student.parent_id.message_post(body=_('Student has been archieved from API'))
        return Response("Deleted", status=204, mimetype="application/json")

    @restapi.webhook(
        input_param=Datamodel("student.payment.item.webhook"),
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
