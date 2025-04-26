# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo import _lt
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class SupplierPaymentPartnerBank(Datamodel):
    _name = "supplier.payment.partner.bank"
    _inherit = "payment.partner.bank"

    merchant = fields.String(required=True, allow_none=False, metadata={"title": "Merchant Name", "description": "Merchant name", "example": "Jane Doe Inc."})


class SupplierPaymentPartnerBank(Datamodel):
    _name = "supplier.payment.partner"

    class Meta:
        ordered = True

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Partner Name"), "description": _lt("Partner name"), "example": "John Doe"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": _lt("Partner VAT"), "description": _lt("Partner VAT number"), "example": "12345678910"})
    email = fields.String(required=True, allow_none=False, metadata={"title": _lt("Email Address"), "description": _lt("Email address"), "example": "test@example.com"})
    phone = fields.String(required=True, allow_none=False, metadata={"title": _lt("Phone Number"), "description": _lt("Phone number"), "example": "+905321234567"})
    country = fields.String(required=False, allow_none=False, metadata={"title": _lt("Country Code"), "description": _lt("Country code"), "example": "TR"})
    state = fields.String(required=False, allow_none=False, metadata={"title": _lt("State Code"), "description": _lt("State code"), "example": "34"})
    city = fields.String(required=False, allow_none=False, metadata={"title": _lt("City/Town Name"), "description": _lt("City/Town name"), "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=False, metadata={"title": _lt("Partner Address"), "description": _lt("Partner address"), "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=False, metadata={"title": _lt("ZIP Code"), "description": _lt("ZIP Code"), "example": "34100"})
    banks = fields.List(NestedModel("supplier.payment.partner.bank"), required=True, allow_none=False, metadata={"title": _lt("Bank Account List"), "description": _lt("List of bank accounts of partner")})


class SupplierPaymentPrepareInput(Datamodel):
    _name = "supplier.payment.prepare.input"
    _inherit = "payment.credential.hash"

    class Meta:
        ordered = True

    id = fields.String(required=True, allow_none=False, metadata={"title": "ID", "description": _lt("Any unique identifier related to your specified record in your database for tracking the payment flow"), "example": '12aaff56a'})
    supplier = NestedModel("supplier.payment.partner", required=True, metadata={"title": _lt("Supplier information related to request"), "description": _lt("Supplier information")})
    amount = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Amount"), "description": _lt("Amount to pay"), "example": 145.3})


class SupplierPaymentPrepareOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "supplier.payment.prepare.output"
    _inherit = "payment.output"

    id = fields.UUID(required=False, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Payment ID"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    url = fields.String(required=False, allow_none=False, metadata={"title": _lt("URL"), "description": _lt("Payment URL which redirects to payment page"), "example": "https://example.com/payment?=LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})
