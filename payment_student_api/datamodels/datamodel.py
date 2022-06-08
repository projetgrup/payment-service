# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
#from odoo.addons.datamodel.fields import NestedModel

class Response(Datamodel):
    _name = "response"

    response_code = fields.Integer(required=True, allow_none=False)
    response_message = fields.String(required=True, allow_none=False)

class ApiKeys(Datamodel):
    _name = "api.keys"

    api_key = fields.String(required=True, allow_none=False)

class ApiSecretKeys(Datamodel):
    _name = "api.secret.keys"
    _inherit = "api.keys"

    secret_key = fields.String(required=True, allow_none=False)

class SchoolSearch(Datamodel):
    _name = "school.search"
    _inherit = "api.keys"

    code = fields.String(required=False, allow_none=False)
    name = fields.String(required=False, allow_none=False)

class ClassSearch(Datamodel):
    _name = "class.search"
    _inherit = "api.keys"

    code = fields.String(required=False, allow_none=False)
    name = fields.String(required=False, allow_none=False)

class StudentSearch(Datamodel):
    _name = "student.search"
    _inherit = "api.keys"

    name = fields.String(required=False, allow_none=False)
    vat = fields.String(required=False, allow_none=False)

class PaymentSearch(Datamodel):
    _name = "payment.search"
    _inherit = "api.keys"

    email = fields.String(required=True, allow_none=False)

class SchoolResponse(Datamodel):
    _name = "school.response"
    _inherit = "response"

    schools = fields.List(fields.Dict)

class ClassResponse(Datamodel):
    _name = "class.response"
    _inherit = "response"

    classes = fields.List(fields.Dict)

class StudentResponse(Datamodel):
    _name = "student.response"
    _inherit = "response"

    students = fields.List(fields.Dict)

class PaymentResponse(Datamodel):
    _name = "payment.response"
    _inherit = "response"

    payments = fields.List(fields.Dict)

class StudentCreate(Datamodel):
    _name = "student.create"
    _inherit = "api.secret.keys"

    name = fields.String(required=True, allow_none=False)
    vat = fields.String(required=True, allow_none=False)
    school_code = fields.String(required=True, allow_none=False)
    bursary_code = fields.String(required=True, allow_none=False)
    parent_name = fields.String(required=True, allow_none=False)
    parent_email = fields.String(required=True, allow_none=False)
    parent_mobile = fields.String(required=True, allow_none=False)
