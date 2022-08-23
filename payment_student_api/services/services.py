# -*- coding: utf-8 -*-
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized
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
            raise Unauthorized("Application key not found")

        page = params.page
        if page < 1:
            raise BadRequest("Page number cannot be lower than 1")

        domain = [("company_id","=", company)]
        if params.name:
            domain.append(("name", "ilike", params.name))
        if params.code:
            domain.append(("code", "ilike", params.code))

        schools = []
        for i in self.env["res.student.school"].sudo().search(domain, offset=PAGE_SIZE*(params.page - 1), limit=100):
            schools.append(dict(id=i.id, name=i.name, code=i.code))
        if not schools:
            raise NotFound("No school records found")
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
            raise Unauthorized("Application key not found")

        page = params.page
        if page < 1:
            raise BadRequest("Page number cannot be lower than 1")

        domain = [("company_id","=", company)]
        if params.name:
            domain.append(("name", "ilike", params.name))
        if params.code:
            domain.append(("code", "ilike", params.code))

        classes = []
        for i in self.env["res.student.class"].sudo().search(domain, offset=PAGE_SIZE*(params.page - 1), limit=100):
            classes.append(dict(id=i.id, name=i.name, code=i.code))
        if not classes:
            raise NotFound("No class records found")
        return ClassResponse(classes=classes, response_code=0, response_message='Success')

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
            raise Unauthorized("Application key not found")

        page = params.page
        if page < 1:
            raise BadRequest("Page number cannot be lower than 1")

        domain = [("company_id","=", company),("system","=", "student"),("parent_id","!=", False),("is_company","=", False)]
        if params.name:
            domain.append(("name", "ilike", params.name))
        if params.vat:
            domain.append(("code", "ilike", params.vat))

        students = []
        for i in self.env["res.partner"].sudo().search(domain, offset=PAGE_SIZE*(params.page - 1), limit=100):
            students.append(dict(id=i.id, name=i.name, vat=i.vat, parent=i.parent_id.name))
        if not students:
            raise NotFound("No student records found")
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
            raise Unauthorized("Application key not found")

        page = params.page
        if page < 1:
            raise BadRequest("Page number cannot be lower than 1")

        payments = []
        domain = [("company_id","=", company),("partner_id.email","=", params.email)]
        for i in self.env["payment.transaction"].sudo().search(domain, offset=PAGE_SIZE*page, limit=100):
            payments.append(dict(id=i.id, date=i.create_date.strftime("%d-%m-%Y"), amount=i.amount, state=i.state))
        if not payments:
            raise NotFound("No payment records found")
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
            raise Unauthorized("Application key not found")

        school = self.env['res.student.school'].sudo().search([('code','=',params.school_code)], limit=1)
        if not school:
            raise NotFound("No school found with given code")

        if params.bursary_code:
            bursary = self.env['res.student.bursary'].sudo().search([('code','=',params.bursary_code)], limit=1)

        classroom = self.env['res.student.class'].sudo().search([('code','=',params.class_code)], limit=1)
        if not classroom:
            raise NotFound("No classroom found with given code")

        parent = self.env['res.partner'].sudo().search([('email','=',params.parent_email)], limit=1)
        if not parent:
            parent = self.env['res.partner'].sudo().create({
                'name': params.parent_name,
                'email': params.parent_email,
                'mobile': params.parent_mobile,
                'is_company': True,
                'parent_id': False,
            })

        if not params.ref:
            raise NotFound("No Ref found with given code")

        STUDENT_PARTNER = self.env['res.partner'].with_context(no_vat_validation=True).sudo()
        student = STUDENT_PARTNER.search([('ref', '=', params.ref)])
        student_val = {
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
            student.write(student_val)
        else:
            student = STUDENT_PARTNER.create(student_val)

        students = [dict(id=student.id, name=student.name, vat=student.vat, parent=student.parent_id.name)]
        return StudentResponse(students=students, response_code=0, response_message='Success')

    # PRIVATE METHODS
    def _auth(self, _company, _apikey, _secretkey=False):
        domain = [('company_id','=',_company),('api_key','=',_apikey)]
        if _secretkey:
            domain.append(('secret_key','=',_secretkey))
        return self.env["payment.acquirer.jetcheckout.api"].sudo().search(domain, limit=1)

    def _create(self, _name):
        return self.env["res.partner"].sudo().create()

    def _get(self, _id):
        return self.env["res.partner"].browse(_id)
