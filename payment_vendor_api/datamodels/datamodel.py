# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class VendorPaymentItemParent(Datamodel):
    _name = "vendor.payment.item.parent"

    name = fields.String(required=True, allow_none=False, metadata={"title": "Vendor Name", "description": "Vendor company name", "example": "Jane Doe Inc."})
    vat = fields.String(required=True, allow_none=False, metadata={"title": "Vendor VAT", "description": "VAT number of related vendor. The value of this field must be identical to its corresponding record in payment system. Otherwise, new vendor will be created with given parameters.", "example": "12345678912"})
    email = fields.String(required=True, allow_none=False, metadata={"title": "Vendor Email", "description": "Email address of related vendor", "example": "test@example.com"})
    mobile = fields.String(required=True, allow_none=False, metadata={"title": "Vendor Mobile", "description": "Mobile phone number of related vendor", "example": "+905001234567"})
    reference = fields.String(required=False, allow_none=False, metadata={"title": "Vendor Reference Number", "description": "Vendor Reference", "example": "ABC01"})
    campaign = fields.String(required=False, allow_none=False, metadata={"title": "Vendor Campaign Name", "description": "Vendor Campaign", "example": "Standard"})


class VendorPaymentItemLine(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.item.line"

    amount = fields.Float(required=True, allow_none=False, metadata={"title": "Amount", "description": "Amount to pay", "example": 1200.0})
    description = fields.String(required=False, allow_none=False, metadata={"title": "Payment Description", "description": "Description about related payment item", "example": "ABC01"})


class VendorPaymentItem(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.item"

    vendor = NestedModel("vendor.payment.item.parent", required=True, metadata={"title": "Vendor Information", "description": "Vendor information of payment item"})
    payments = fields.List(NestedModel("vendor.payment.item.line"), required=True, metadata={"title": "Payment Information", "description": "Payment item details which contains amounts and other informations"})


class VendorPaymentCreate(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.create"
    _inherit = "payment.credential.hash"

    items = fields.List(NestedModel("vendor.payment.item"), required=True, allow_none=False, metadata={"title": "Payment List", "description": "List of payment items"})


class VendorPaymentResult(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.result"

    vat = fields.String(metadata={"title": "Vendor VAT", "description": "VAT number of related vendor", "example": "12345678912"})
    link = fields.String(metadata={"title": "Vendor Payment Link", "description": "Payment Link URL address of related vendor", "example": "https://yourdomain.com/p/8850dd69-4496-45b2-bc13-9b47ad939d81"})

class VendorPaymentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.output"
    _inherit = "payment.output"

    result = fields.List(NestedModel("vendor.payment.result"), metadata={"title": "Result", "description": "Detailed result for related request"})


class VendorPaymentItemWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.item.webhook"
    _inherit = "system.payment.item.webhook"
