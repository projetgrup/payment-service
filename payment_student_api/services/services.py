# -*- coding: utf-8 -*-
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.base_rest.controllers import main
from odoo.addons.component.core import Component
from odoo import _

RESPONSE = {
    "success": {
        "response_code": 0,
        "response_message": "İşlem Başarılı",
    },
    "no_api_key": {
        "response_code": 9,
        "response_message": "API Anahtarı bulunamadı",
    },
    "no_school": {
        "response_code": 8,
        "response_message": "Belirtilen okul bulunamadı",
    },
    "no_bursary": {
        "response_code": 7,
        "response_message": "Belirtilen burs bulunamadı",
    },
    "no_payment": {
        "response_code": 6,
        "response_message": "Ödeme bulunamadı",
    },
}


class StudentAPIController(main.RestController):
    _root_path = "/api/v1/"
    _collection_name = "student.api.services"
    _default_auth = "public"


class StudentAPIService(Component):
    _inherit = "base.rest.service"
    _name = "student.api.service"
    _usage = "student"
    _collection = "student.api.services"
    _description = """Öğrenci API Servisleri"""

    @restapi.method(
        [(["/school"], "POST")],
        input_param=Datamodel("school.search"),
        output_param=Datamodel("school.response"),
        auth="public",
    )
    def list_school(self, params):
        """
        Okul Listele
        :param params: Okul Kodu
        :return: Okul Listesi
        """
        SchoolResponse = self.env.datamodels["school.response"]
        company = self.env.company.id
        key = self._auth(company, params.api_key)
        if not key:
            return SchoolResponse(**RESPONSE['no_api_key'])

        domain = [("company_id","=", company)]
        if params.name:
            domain.append(("name", "like", params.name))
        if params.code:
            domain.append(("code", "=", params.code))

        schools = []
        for i in self.env["res.student.school"].search(domain):
            schools.append(dict(id=i.id, name=i.name, code=i.code))
        return SchoolResponse(schools=schools,**RESPONSE['success'])

    @restapi.method(
        [(["/class"], "POST")],
        input_param=Datamodel("class.search"),
        output_param=Datamodel("class.response"),
        auth="public",
    )
    def list_class(self, params):
        """
        Sınıf Listele
        :param params: Sınıf Kodu
        :return: Sınıf Listesi
        """
        ClassResponse = self.env.datamodels["class.response"]
        company = self.env.company.id
        key = self._auth(company, params.api_key)
        if not key:
            return ClassResponse(**RESPONSE["no_api_key"])

        domain = [("company_id","=", company)]
        if params.name:
            domain.append(("name", "like", params.name))
        if params.code:
            domain.append(("code", "=", params.code))

        classes = []
        for i in self.env["res.student.class"].search(domain):
            classes.append(dict(id=i.id, name=i.name, code=i.code))
        return ClassResponse(classes=classes,**RESPONSE["success"])

    @restapi.method(
        [(["/"], "POST")],
        input_param=Datamodel("student.search"),
        output_param=Datamodel("student.response"),
        auth="public",
    )
    def list_student(self, params):
        """
        Öğrenci ve Veli Listele
        :param params: Adı, TCKN
        :return: Öğrenci Listesi
        """
        StudentResponse = self.env.datamodels["student.response"]
        company = self.env.company.id
        key = self._auth(company, params.api_key)
        if not key:
            return StudentResponse(**RESPONSE["no_api_key"])

        domain = [("company_id","=", company),("system","=", "student"),("parent_id","!=", False),("is_company","=", False)]
        if params.name:
            domain.append(("name", "like", params.name))
        if params.vat:
            domain.append(("code", "ilike", params.vat))

        students = []
        for i in self.env["res.partner"].search(domain):
            students.append(dict(id=i.id, name=i.name, vat=i.vat, parent=i.parent_id.name))
        return StudentResponse(students=students,**RESPONSE["success"])

    @restapi.method(
        [(["/payment"], "POST")],
        input_param=Datamodel("payment.search"),
        output_param=Datamodel("payment.response"),
        auth="public",
    )
    def list_payment(self, params):
        """
        Ödeme Listele
        :param params: Veli Eposta
        :return: Ödeme Listesi
        """
        PaymentResponse = self.env.datamodels["payment.response"]
        company = self.env.company.id
        key = self._auth(company, params.api_key)
        if not key:
            return PaymentResponse(**RESPONSE["no_api_key"])

        domain = [("company_id","=", company),("partner_id.email","=", params.email)]

        payments = []
        for i in self.env["payment.transaction"].search(domain):
            payments.append(dict(id=i.id, date=i.create_date.strftime("%d-%m-%Y"), amount=i.amount, state=i.state))
        if not payments:
            return PaymentResponse(**RESPONSE["no_payment"])
        return PaymentResponse(payments=payments,**RESPONSE["success"])

    @restapi.method(
        [(["/create"], "POST")],
        input_param=Datamodel("student.create"),
        output_param=Datamodel("student.response"),
        auth="public",
    )
    def create_student(self, params):
        """
        Öğrenci ve Veli Listele
        :param params: name, vat, school_code, bursary_code, parent_name, parent_email, parent_mobile
        :return: Oluşan Öğrencilerin Listesi
        """
        StudentResponse = self.env.datamodels["student.response"]
        company = self.env.company.id
        key = self._auth(company, params.api_key, params.secret_key)
        if not key:
            return StudentResponse(**RESPONSE["no_api_key"])

        school = self.env['res.student.school'].sudo().search([('code','=',params.school_code)], limit=1)
        if not school:
            return StudentResponse(**RESPONSE["no_school"])

        bursary = self.env['res.student.bursary'].sudo().search([('code','=',params.bursary_code)], limit=1)
        if not bursary:
            return StudentResponse(**RESPONSE["no_bursary"])

        parent = self.env['res.partner'].sudo().search([('email','=',params.parent_email)], limit=1)
        if not parent:
            parent = self.env['res.partner'].sudo().create({
                'name': params.parent_name,
                'email': params.parent_email,
                'mobile': params.parent_mobile,
                'is_company': True,
                'parent_id': False,
            })

        student = self.env['res.partner'].sudo().create({
            'name': params.name,
            'vat': params.vat,
            'school_id': school.id,
            'bursary_id': bursary.id,
            'parent_id': parent.id,
            'is_company': False,
        })

        students = [dict(id=student.id, name=student.name, vat=student.vat, parent=student.parent_id.name)]
        return StudentResponse(students=students,**RESPONSE["success"])

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
