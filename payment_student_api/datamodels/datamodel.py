# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel

class Response(Datamodel):
    class Meta:
        ordered = True

    _name = "response"

    response_code = fields.Integer(required=True, allow_none=False, title="Response Code", description="Integer which is returned to represent response", example=0)
    response_message = fields.String(required=True, allow_none=False, title="Response Message", description="Description which is returned to represent response", example="Success")

class ApiKeys(Datamodel):
    class Meta:
        ordered = True

    _name = "api.keys"

    application_key = fields.String(required=True, allow_none=False, title="Application Key", description="API Key which is acquired by your service provider", example="1x2cdaa3-35df-2eff-aeq2-5d74387701xd")

class ApiSecretKeys(Datamodel):
    class Meta:
        ordered = True

    _name = "api.secret.keys"
    _inherit = "api.keys"

    secret_key = fields.String(required=True, allow_none=False, title="Secret Key", description="Secret Key which is given to you by your service provider", example="xa18a2325z80c73ay871au54ba169c76")

class SchoolSearch(Datamodel):
    class Meta:
        ordered = True

    _name = "school.search"
    _inherit = "api.keys"

    page = fields.Integer(required=True, allow_none=False, title="Page Number", description="Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", example="1")
    code = fields.String(required=False, allow_none=False, title="School Code", description="A part of school code can be entered. For example, when you enter 'JOH', the codes which contain this word will be listed. It is not a required field.", example="JOHNDC")
    name = fields.String(required=False, allow_none=False, title="School Name", description="A part of school name can be entered. For example, when you enter 'College', the names which contain this word will be listed. It is not a required field.", example="John Doe College")

class ClassSearch(Datamodel):
    class Meta:
        ordered = True

    _name = "class.search"
    _inherit = "api.keys"

    page = fields.Integer(required=True, allow_none=False, title="Page Number", description="Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", example="1")
    code = fields.String(required=False, allow_none=False, title="Class Code", description="A part of class code can be entered. For example, when you enter 'CLA', the codes which contain this word will be listed. It is not a required field.", example="CLASS1")
    name = fields.String(required=False, allow_none=False, title="Class Name", description="A part of class name can be entered. For example, when you enter 'Clas', the names which contain this word will be listed. It is not a required field.", example="Class 1")

class BursarySearch(Datamodel):
    class Meta:
        ordered = True

    _name = "bursary.search"
    _inherit = "api.keys"

    page = fields.Integer(required=True, allow_none=False, title="Page Number", description="Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", example="1")
    code = fields.String(required=False, allow_none=False, title="Bursary Code", description="A part of bursary code can be entered. For example, when you enter 'BUR', the codes which contain this word will be listed. It is not a required field.", example="BURSARY50")
    name = fields.String(required=False, allow_none=False, title="Bursary Name", description="A part of bursary name can be entered. For example, when you enter 'Clas', the names which contain this word will be listed. It is not a required field.", example="Bursary 50%")

class StudentSearch(Datamodel):
    class Meta:
        ordered = True

    _name = "student.search"
    _inherit = "api.keys"

    page = fields.Integer(required=True, allow_none=False, title="Page Number", description="Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", example="1")
    name = fields.String(required=False, allow_none=False, title="Student Name", description="Student name", example="Jane Doe")
    vat = fields.String(required=False, allow_none=False, title="Student ID Number", description="Student citizen number", example="12345678912")

class PaymentSearch(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.search"
    _inherit = "api.keys"

    page = fields.Integer(required=True, allow_none=False, title="Page Number", description="Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", example="1")
    email = fields.String(required=True, allow_none=False, title="Email", description="Email address", example="test@example.com")

class SchoolResponse(Datamodel):
    class Meta:
        ordered = True

    _name = "school.response"
    _inherit = "response"

    schools = fields.List(fields.Dict, title="Schools", description="List of schools", example=[{"id": 26, "name": "John Doe College", "code": "JOHNDC"}])

class ClassResponse(Datamodel):
    class Meta:
        ordered = True

    _name = "class.response"
    _inherit = "response"

    classes = fields.List(fields.Dict, title="Classes", description="List of classes", example=[{"id": 34, "name": "Class 1", "code": "CLASS1"}])

class BursaryResponse(Datamodel):
    class Meta:
        ordered = True

    _name = "bursary.response"
    _inherit = "response"

    bursaries = fields.List(fields.Dict, title="Bursaries", description="List of bursaries", example=[{"id": 12, "name": "Bursary 50%", "code": "BURSARY50"}])

class StudentResponse(Datamodel):
    class Meta:
        ordered = True

    _name = "student.response"
    _inherit = "response"

    students = fields.List(fields.Dict, title="Students", description="List of students", example=[{"id": 52, "name": "Jane Doe", "vat": "12345678912", "parent": "John Doe"}])

class PaymentResponse(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.response"
    _inherit = "response"

    payments = fields.List(fields.Dict, title="Payments", description="List of payments", example=[{"id": 76, "date": "25-01-2021", "amount": 145.30, "state": "done"}])


class StudentCreate(Datamodel):
    class Meta:
        ordered = True

    _name = "student.create"
    _inherit = "api.secret.keys"

    name = fields.String(required=True, allow_none=False, title="Student Name", description="Student name", example="Jane Doe")
    vat = fields.String(required=True, allow_none=False, title="Student ID Number", description="Student citizen number", example="12345678912")
    school_code = fields.String(required=True, allow_none=False, title="School Code", description="School codename", example="JOHNDC")
    bursary_code = fields.String(allow_none=True, title="Bursary Code", description="Bursary codename", example="BURSARY50")
    class_code = fields.String(required=True, allow_none=False, title="Class Code", description="Class codename", example="CLASS1")
    parent_name = fields.String(required=True, allow_none=False, title="Parent Name", description="Parent name of related student", example="John Doe")
    parent_email = fields.String(required=True, allow_none=False, title="Parent Email", description="Email address of related parent", example="test@example.com")
    parent_mobile = fields.String(required=True, allow_none=False, title="Parent Mobile", description="Mobile phone number of related parent", example="+905001234567")
    ref = fields.String(required=True, allow_none=False, title="Ref", description="Student your REF number", example="ABC01")


class StudentDelete(Datamodel):
    class Meta:
        ordered = True

    _name = "student.delete"
    _inherit = "api.secret.keys"

    vat = fields.String(required=False, allow_none=False, title="Student Citizen Number", description="Citizen number on student form", example="12345678912")
    ref = fields.String(required=False, allow_none=False, title="Student Reference Number", description="Reference on student form", example="123456789")


class StudentWebhookParent(Datamodel):
    class Meta:
        ordered = True

    _name = "student.webhook.parent"

    name = fields.String(title="Parent Name", description="Parent name", example="Jane Doe", required=True)
    vat = fields.String(title="Parent VAT", description="Parent citizen number", example="12345678912", required=True)


class StudentWebhookItemChild(Datamodel):
    class Meta:
        ordered = True

    _name = "student.webhook.item.child"

    name = fields.String(title="Student Name", description="Student name", example="John Doe", required=True)
    vat = fields.String(title="Student VAT", description="Student citizen number", example="12345678912", required=True)
    ref = fields.String(title="Student Reference", description="Student reference", example="CODE12", required=True)


class StudentWebhookItemBursary(Datamodel):
    class Meta:
        ordered = True

    _name = "student.webhook.item.bursary"

    name = fields.String(title="Bursary Name", description="Bursary name", example="Management Bursary", required=True)
    code = fields.String(title="Bursary Code", description="Bursary code", example="BURSARY50", required=True)
    discount = fields.Integer(title="Bursary Discount Percentage", description="Bursary discount percentage", example=10, required=True)


class StudentWebhookItemAmountDiscount(Datamodel):
    class Meta:
        ordered = True

    _name = "student.webhook.item.amount.discount"

    bursary = fields.Float(title="Bursary Discount Amount", description="Bursary discount amount", example=120.0, required=True)
    prepayment = fields.Float(title="Prepayment Discount Amount", description="Prepayment discount amount", example=80.0, required=True)


class StudentWebhookItemAmount(Datamodel):
    class Meta:
        ordered = True

    _name = "student.webhook.item.amount"

    total = fields.Float(title="Total Amount", description="Total amount", example=2200.0, required=True)
    discount = NestedModel("student.webhook.item.amount.discount", title="Discount Information", description="Discount information", required=True)
    paid = fields.Float(title="Payment Amount", description="Payment amount", example=2000.0, required=True)


class StudentWebhookItems(Datamodel):
    class Meta:
        ordered = True

    _name = "student.webhook.item"

    student = NestedModel("student.webhook.item.child", title="Student Information", description="Student information", required=True)
    bursary = NestedModel("student.webhook.item.bursary", title="Bursary Information", description="Bursary information", required=True)
    amount = NestedModel("student.webhook.item.amount", title="Amount Information", description="Amount information", required=True)


class StudentWebhookCard(Datamodel):
    class Meta:
        ordered = True

    _name = "student.webhook.card"

    family = fields.String(title="Credit Card Family", description="Credit card family", example="Paraf", required=True)
    vpos = fields.String(title="Virtual PoS Name", description="Virtual pos name", example="General", required=True)


class StudentWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "student.webhook"

    parent = NestedModel("student.webhook.parent", title="Parent Information", description="Parent information", required=True)
    items = fields.List(NestedModel("student.webhook.item"), title="Student Name", description="Student name", required=True)
    card = NestedModel("student.webhook.card", title="Card Information", description="Card information", required=True)