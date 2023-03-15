# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel

class StudentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.output"

    response_code = fields.Integer(required=True, allow_none=False, metadata={"title": "Response Code", "description": "Integer which is returned to represent response", "example": 0})
    response_message = fields.String(required=True, allow_none=False, metadata={"title": "Response Message", "description": "Description which is returned to represent response", "example": "Success"})

class StudentCredentialApikey(Datamodel):
    class Meta:
        ordered = True

    _name = "student.credential.apikey"

    application_key = fields.String(required=True, allow_none=False, metadata={"title": "Application Key", "description": "API Key which is acquired by your service provider", "example": "1x2cdaa3-35df-2eff-aeq2-5d74387701xd"})

class StudentCredentialSecretkey(Datamodel):
    class Meta:
        ordered = True

    _name = "student.credential.secretkey"
    _inherit = "student.credential.apikey"

    secret_key = fields.String(required=True, allow_none=False, metadata={"title": "Secret Key", "description": "Secret Key which is given to you by your service provider", "example": "xa18a2325z80c73ay871au54ba169c76"})

class StudentSchoolInput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.school.input"
    _inherit = "student.credential.apikey"

    page = fields.Integer(required=True, allow_none=False, metadata={"title": "Page Number", "description": "Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", "example": "1"})
    code = fields.String(required=False, allow_none=False, metadata={"title": "School Code", "description": "A part of school code can be entered. For example, when you enter 'JOH', the codes which contain this word will be listed. It is not a required field.", "example": "JOHNDC"})
    name = fields.String(required=False, allow_none=False, metadata={"title": "School Name", "description": "A part of school name can be entered. For example, when you enter 'College', the names which contain this word will be listed. It is not a required field.", "example": "John Doe College"})

class StudentClassInput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.class.input"
    _inherit = "student.credential.apikey"

    page = fields.Integer(required=True, allow_none=False, metadata={"title": "Page Number", "description": "Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", "example": "1"})
    code = fields.String(required=False, allow_none=False, metadata={"title": "Class Code", "description": "A part of class code can be entered. For example, when you enter 'CLA', the codes which contain this word will be listed. It is not a required field.", "example": "CLASS1"})
    name = fields.String(required=False, allow_none=False, metadata={"title": "Class Name", "description": "A part of class name can be entered. For example, when you enter 'Clas', the names which contain this word will be listed. It is not a required field.", "example": "Class 1"})

class StudentBursaryInput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.bursary.input"
    _inherit = "student.credential.apikey"

    page = fields.Integer(required=True, allow_none=False, metadata={"title": "Page Number", "description": "Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", "example": "1"})
    code = fields.String(required=False, allow_none=False, metadata={"title": "Bursary Code", "description": "A part of bursary code can be entered. For example, when you enter 'BUR', the codes which contain this word will be listed. It is not a required field.", "example": "BURSARY50"})
    name = fields.String(required=False, allow_none=False, metadata={"title": "Bursary Name", "description": "A part of bursary name can be entered. For example, when you enter 'Burs', the names which contain this word will be listed. It is not a required field.", "example": "Bursary 50%"})

class StudentChildInput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.child.input"
    _inherit = "student.credential.apikey"

    page = fields.Integer(required=True, allow_none=False, metadata={"title": "Page Number", "description": "Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", "example": "1"})
    name = fields.String(required=False, allow_none=False, metadata={"title": "Student Name", "description": "Student name", "example": "Jane Doe"})
    vat = fields.String(required=False, allow_none=False, metadata={"title": "Student ID Number", "description": "Student citizen number", "example": "12345678912"})

class StudentPaymentInput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.payment.input"
    _inherit = "student.credential.apikey"

    page = fields.Integer(required=True, allow_none=False, metadata={"title": "Page Number", "description": "Records are paged hundred by hundred. Given page number will be used when getting desired records. First page starts with 1.", "example": "1"})
    email = fields.String(required=True, allow_none=False, metadata={"title": "Email", "description": "Email address", "example": "test@example.com"})

class StudentSchoolOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.school.output"
    _inherit = "student.output"

    schools = fields.List(fields.Dict, metadata={"title": "Schools", "description": "List of schools", "example": [{"id": 26, "name": "John Doe College", "code": "JOHNDC"}]})

class StudentClassOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.class.output"
    _inherit = "student.output"

    classes = fields.List(fields.Dict, metadata={"title": "Classes", "description": "List of classes", "example": [{"id": 34, "name": "Class 1", "code": "CLASS1"}]})

class StudentBursaryOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.bursary.output"
    _inherit = "student.output"

    bursaries = fields.List(fields.Dict, metadata={"title": "Bursaries", "description": "List of bursaries", "example": [{"id": 12, "name": "Bursary 50%", "code": "BURSARY50"}]})

class StudentChildOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.child.output"
    _inherit = "student.output"

    students = fields.List(fields.Dict, metadata={"title": "Students", "description": "List of students", "example": [{"id": 52, "name": "Jane Doe", "vat": "12345678912", "parent": "John Doe"}]})

class StudentPaymentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "student.payment.output"
    _inherit = "student.output"

    payments = fields.List(fields.Dict, metadata={"title": "Payments", "description": "List of payments", "example": [{"id": 76, "date": "25-01-2021", "amount": 145.3, "state": "done"}]})


class StudentChildCreate(Datamodel):
    class Meta:
        ordered = True

    _name = "student.child.create"
    _inherit = "student.credential.secretkey"

    name = fields.String(required=True, allow_none=False, metadata={"title": "Student Name", "description": "Student name", "example": "Jane Doe"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": "Student ID Number", "description": "Student citizen number", "example": "12345678912"})
    ref = fields.String(required=True, allow_none=False, metadata={"title": "Student Reference", "description": "Student reference number", "example": "ABC01"})
    school_code = fields.String(required=True, allow_none=False, metadata={"title": "School Code", "description": "School codename", "example": "JOHNDC"})
    bursary_code = fields.String(allow_none=True, metadata={"title": "Bursary Code", "description": "Bursary codename", "example": "BURSARY50"})
    class_code = fields.String(required=True, allow_none=False, metadata={"title": "Class Code", "description": "Class codename", "example": "CLASS1"})
    term_code = fields.String(required=False, allow_none=False, metadata={"title": "Term Code", "description": "Term codename", "example": "TERM7"})
    parent_name = fields.String(required=True, allow_none=False, metadata={"title": "Parent Name", "description": "Parent name of related student", "example": "John Doe"})
    parent_email = fields.String(required=True, allow_none=False, metadata={"title": "Parent Email", "description": "Email address of related parent", "example": "test@example.com"})
    parent_mobile = fields.String(required=True, allow_none=False, metadata={"title": "Parent Mobile", "description": "Mobile phone number of related parent", "example": "+905001234567"})
    campaign_name = fields.String(required=False, allow_none=False, metadata={"title": "Campaign", "description": "Campaign name", "example": "New Year Campaign"})


class StudentChildDelete(Datamodel):
    class Meta:
        ordered = True

    _name = "student.child.delete"
    _inherit = "student.credential.secretkey"

    vat = fields.String(required=False, allow_none=False, metadata={"title": "Student Citizen Number", "description": "Citizen number on student form", "example": "12345678912"})
    ref = fields.String(required=False, allow_none=False, metadata={"title": "Student Reference Number", "description": "Reference on student form", "example": "123456789"})


class StudentPaymentItemChild(Datamodel):
    class Meta:
        ordered = True

    _name = "student.payment.item.child"
    _inherit = "system.payment.item.child"

    name = fields.String(required=True, metadata={"title": "Student Name", "description": "Student name and surname", "example": "John Doe"})
    vat = fields.String(required=True, metadata={"title": "Student VAT", "description": "Student citizen number", "example": "12345678912"})
    reference = fields.String(required=True, metadata={"title": "Student Reference", "description": "Student reference details", "example": "CODE12"})


class StudentPaymentItemBursary(Datamodel):
    class Meta:
        ordered = True

    _name = "student.payment.item.bursary"

    name = fields.String(metadata={"title": "Bursary Name", "description": "Student bursary name", "example": "Management Bursary"})
    code = fields.String(metadata={"title": "Bursary Code", "description": "Student bursary code", "example": "BURSARY50"})
    discount = fields.Integer(metadata={"title": "Bursary Discount Percentage", "description": "Student bursary discount percentage", "example": 10})


class StudentPaymentItemAmountDiscount(Datamodel):
    class Meta:
        ordered = True

    _name = "student.payment.item.amount.discount"
    _inherit = "system.payment.item.amount.discount"

    bursary = fields.Float(required=True, metadata={"title": "Bursary Discount Amount", "description": "Bursary discount amount of payment item", "example": 120.0})


class StudentPaymentItemAmount(Datamodel):
    class Meta:
        ordered = True

    _name = "student.payment.item.amount"
    _inherit = "system.payment.item.amount"

    discount = NestedModel("student.payment.item.amount.discount", required=True, metadata={"title": "Discount details of payment transaction", "description": "Discount information"})


class StudentPaymentItem(Datamodel):
    class Meta:
        ordered = True

    _name = "student.payment.item"
    _inherit = "system.payment.item"

    student = NestedModel("student.payment.item.child", required=True, metadata={"title": "Student Information", "description": "Student details related to parent"})
    bursary = NestedModel("student.payment.item.bursary", required=True, metadata={"title": "Bursary Information", "description": "Bursary details of related student"})
    amount = NestedModel("student.payment.item.amount", required=True, metadata={"title": "Amount Information", "description": "Amount details of payment transaction"})


class StudentPaymentItemWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "student.payment.item.webhook"
    _inherit = "system.payment.item.webhook"

    items = fields.List(NestedModel("student.payment.item"), required=True, metadata={"title": "Payment Information", "description": "Payment item details which contains amounts and other informations"})
