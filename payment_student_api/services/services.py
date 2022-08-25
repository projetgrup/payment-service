# -*- coding: utf-8 -*-
from odoo.http import Response
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component
from odoo import _

PAGE_SIZE = 100


class StudentAPIService(Component):
    _inherit = "base.rest.service"
    _name = "student"
    _usage = "student"
    _collection = "payment"
    _description = """This API helps you connect student payment system with your specially generated key"""

    @restapi.method(
        [(["/schools"], "GET")],
        input_param=Datamodel("school.search"),
        output_param=Datamodel("school.response"),
        auth="public",
    )
    def list_school(self, params):
        """
        List Schools
        tags: ['List Methods']
        """
        SchoolResponse = self.env.datamodels["school.response"]
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
        for i in self.env["res.student.school"].sudo().search(domain, offset=PAGE_SIZE * page, limit=100):
            schools.append(dict(id=i.id, name=i.name, code=i.code))
        if not schools:
            return Response("No records found", status=404, mimetype="application/json")
        return SchoolResponse(schools=schools, response_code=0, response_message='Success')

    @restapi.method(
        [(["/classes"], "GET")],
        input_param=Datamodel("class.search"),
        output_param=Datamodel("class.response"),
        auth="public",
    )
    def list_class(self, params):
        """
        List Classes
        tags: ['List Methods']
        """
        ClassResponse = self.env.datamodels["class.response"]
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
        for i in self.env["res.student.class"].sudo().search(domain, offset=PAGE_SIZE * page, limit=100):
            classes.append(dict(id=i.id, name=i.name, code=i.code))
        if not classes:
            return Response("No records found", status=404, mimetype="application/json")
        return ClassResponse(classes=classes, response_code=0, response_message='Success')

    @restapi.method(
        [(["/bursaries"], "GET")],
        input_param=Datamodel("bursary.search"),
        output_param=Datamodel("bursary.response"),
        auth="public",
    )
    def list_bursary(self, params):
        """
        List Bursaries
        tags: ['List Methods']
        """
        BursaryResponse = self.env.datamodels["bursary.response"]
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
        for i in self.env["res.student.bursary"].sudo().search(domain, offset=PAGE_SIZE * page, limit=100):
            bursaries.append(dict(id=i.id, name=i.name, code=i.code))
        if not bursaries:
            return Response("No records found", status=404, mimetype="application/json")
        return BursaryResponse(bursaries=bursaries, response_code=0, response_message='Success')

    @restapi.method(
        [(["/students"], "GET")],
        input_param=Datamodel("student.search"),
        output_param=Datamodel("student.response"),
        auth="public",
    )
    def list_student(self, params):
        """
        List Students And Parents
        tags: ['List Methods']
        """
        StudentResponse = self.env.datamodels["student.response"]
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
        for i in self.env["res.partner"].sudo().search(domain, offset=PAGE_SIZE * page, limit=100):
            students.append(dict(id=i.id, name=i.name, vat=i.vat, parent=i.parent_id.name))
        if not students:
            return Response("No records found", status=404, mimetype="application/json")
        return StudentResponse(students=students, response_code=0, response_message='Success')

    @restapi.method(
        [(["/payments"], "GET")],
        input_param=Datamodel("payment.search"),
        output_param=Datamodel("payment.response"),
        auth="public",
    )
    def list_payment(self, params):
        """
        List Payments
        tags: ['List Methods']
        """
        PaymentResponse = self.env.datamodels["payment.response"]
        company = self.env.company.id
        key = self._auth(company, params.application_key)
        if not key:
            return Response("Application key is not matched", status=401, mimetype="application/json")

        page = params.page - 1
        if page < 0:
            return Response("Page number cannot be lower than 1", status=400, mimetype="application/json")

        payments = []
        domain = [("company_id", "=", company), ("partner_id.email", "=", params.email)]
        for i in self.env["payment.transaction"].sudo().search(domain, offset=PAGE_SIZE * page, limit=100):
            payments.append(dict(id=i.id, date=i.create_date.strftime("%d-%m-%Y"), amount=i.amount, state=i.state))
        if not payments:
            return Response("No records found", status=404, mimetype="application/json")
        return PaymentResponse(payments=payments, response_code=0, response_message='Success')

    @restapi.method(
        [(["/create"], "POST")],
        input_param=Datamodel("student.create"),
        output_param=Datamodel("student.response"),
        auth="public",
    )
    def create_student(self, params):
        """
        Create Student
        tags: ['Create Methods']
        """
        StudentResponse = self.env.datamodels["student.response"]
        company = self.env.company.id
        key = self._auth(company, params.application_key, params.secret_key)
        if not key:
            return Response("Application key and secret key are not matched", status=401, mimetype="application/json")

        school = self.env['res.student.school'].sudo().search([('code', '=', params.school_code)], limit=1)
        if not school:
            return Response("No school found with given code", status=404, mimetype="application/json")

        bursary = self.env['res.student.bursary'].sudo()
        if hasattr(params, 'bursary_code') and params.bursary_code:
            bursary = bursary.search([('code', '=', params.bursary_code)], limit=1)

        classroom = self.env['res.student.class'].sudo().search([('code', '=', params.class_code)], limit=1)
        if not classroom:
            return Response("No classroom found with given code", status=404, mimetype="application/json")

        parent = self.env['res.partner'].sudo().search([('email', '=', params.parent_email)], limit=1)
        if not parent:
            parent = self.env['res.partner'].sudo().create({
                'name': params.parent_name,
                'email': params.parent_email,
                'mobile': params.parent_mobile,
                'is_company': True,
                'parent_id': False,
            })

        if not params.ref:
            return Response("No ref found with given code", status=404, mimetype="application/json")

        students = self.env['res.partner'].with_context({'no_vat_validation': True, 'active_system': 'student'}).sudo()
        student = students.search([('ref', '=', params.ref)])
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
        }
        if student:
            student.write(vals)
        else:
            student = students.create(vals)

        students = [dict(id=student.id, name=student.name, vat=student.vat, parent=student.parent_id.name)]
        return StudentResponse(students=students, response_code=0, response_message='Success')

    @restapi.method(
        [(["/delete"], "DELETE")],
        input_param=Datamodel("student.delete"),
        auth="public",
    )
    def delete_student(self, params):
        """
        Delete Student
        tags: ['Delete Methods']
        """
        company = self.env.company.id
        key = self._auth(company, params.application_key, params.secret_key)
        if not key:
            return Response("Application key and secret key are not matched", status=401, mimetype="application/json")

        student = self.env['res.partner'].sudo().search([('company_id', '=', company), ('vat', '=ilike', '%%%s' % params.vat)], limit=1)
        if not student:
            return Response("No student found with given citizen number", status=404, mimetype="application/json")
        if len(student.payment_ids) + len(student.paid_ids) > 0:
            return Response("Student who has payment items cannot be deleted", status=400, mimetype="application/json")

        student.unlink()
        return Response("Deleted", status=204, mimetype="application/json")

    # PRIVATE METHODS
    def _auth(self, _company, _apikey, _secretkey=False):
        domain = [('company_id', '=', _company), ('api_key', '=', _apikey)]
        if _secretkey:
            domain.append(('secret_key', '=', _secretkey))
        return self.env["payment.acquirer.jetcheckout.api"].sudo().search(domain, limit=1)

    def _create(self, _name):
        return self.env["res.partner"].sudo().create()

    def _get(self, _id):
        return self.env["res.partner"].browse(_id)
