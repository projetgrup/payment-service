# -*- coding: utf-8 -*-
from odoo import _lt
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class OcoPaymentPartner(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.partner"

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Partner Name"), "description": _lt("Partner name"), "example": "John Doe"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": _lt("Partner VAT"), "description": _lt("Partner VAT number"), "example": "12345678910"})
    email = fields.String(required=True, allow_none=False, metadata={"title": _lt("Email Address"), "description": _lt("Email address"), "example": "test@example.com"})
    phone = fields.String(required=True, allow_none=False, metadata={"title": _lt("Phone Number"), "description": _lt("Phone number"), "example": "+905321234567"})
    ip_address = fields.String(required=True, allow_none=False, metadata={"title": _lt("IP Address"), "description": _lt("IP Address"), "example": "34.06.50.01"})
    country = fields.String(required=False, allow_none=False, metadata={"title": _lt("Country Code"), "description": _lt("Country code"), "example": "TR"})
    state = fields.String(required=False, allow_none=False, metadata={"title": _lt("State Code"), "description": _lt("State code"), "example": "34"})
    city = fields.String(required=False, allow_none=True, metadata={"title": _lt("City/Town Name"), "description": _lt("City/Town name"), "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=False, metadata={"title": _lt("Partner Address"), "description": _lt("Partner address"), "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=True, metadata={"title": _lt("ZIP Code"), "description": _lt("ZIP Code"), "example": "34100"})
    contact = fields.String(required=False, allow_none=False, metadata={"title": _lt("Contact Name"), "description": _lt("Contact name"), "example": "Jane Doe"})


class OcoPaymentCompany(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.company"

    vat = fields.String(required=True, allow_none=False, metadata={"title": _lt("Company VAT"), "description": _lt("Company VAT number"), "example": "12345678910"})


class OcoPaymentOrder(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.order"

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Order Name"), "description": _lt("Order name"), "example": "S123564"})
    products = fields.List(NestedModel("payment.product"), required=False, metadata={"title": _lt("Products List"), "description": _lt("List of related products")})


class OcoPaymentUrl(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.url"

    card = NestedModel("payment.url.method", required=True, metadata={"title": _lt("Return URLs by card payment method"), "description": _lt("URL addresses when card payment is selected")})
    bank = NestedModel("payment.url.method", required=False, metadata={"title": _lt("Return URLs by bank payment method"), "description": _lt("URL addresses when bank payment is selected")})


class OrderCheckoutPaymentCreate(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.create"
    _inherit = "payment.credential.hash"

    id = fields.Integer(required=True, allow_none=False, metadata={"title": "ID", "description": _lt("Any unique number related to your specified record in your database for tracking the payment flow"), "example": 12})
    expiration = fields.DateTime(allow_none=False, metadata={"title": _lt("Expiration Date"), "description": _lt("Datetime in ISO format to get transaction expired"), "example": "2023-01-01T00:00:00"})
    campaign = fields.String(metadata={"title": _lt("Campaign Name"), "description": _lt("Name of campaign to be used in getting installment options"), "example": "Standard"})
    company = NestedModel("oco.payment.company", required=True, metadata={"title": _lt("Company information related to request"), "description": _lt("Company information")})
    partner = NestedModel("oco.payment.partner", required=True, metadata={"title": _lt("Partner information related to request"), "description": _lt("Partner information")})
    order = NestedModel("oco.payment.order", required=True, metadata={"title": _lt("Order information related to request"), "description": _lt("Order details")})
    url = NestedModel("oco.payment.url", required=True, metadata={"title": _lt("Return URLs by payment method"), "description": _lt("URL addresses")})
    html = fields.String(metadata={"title": _lt("Custom HTML"), "description": _lt("Custom code to be viewed bottom of the page"), "example": "<p>Copyright</p>"})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Amount"), "description": _lt("Amount to pay"), "example": 145.3})
    methods = fields.List(fields.String(), required=False, allow_none=False, metadata={"title": _lt("Method List"), "description": _lt("List of codes of methods. Possible values are 'card' and 'bank'."), "example": ["bank", "card"]})


class OrderCheckoutPaymentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.output"
    _inherit = "payment.output"

    hash = fields.String(required=False, allow_none=False, metadata={"title": _lt("Hash Data"), "description": _lt("Encrypted data to check if hash is created successfully"), "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})
