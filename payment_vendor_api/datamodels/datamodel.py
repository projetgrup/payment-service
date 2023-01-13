# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class VendorPaymentItemLine(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.item"

    name = fields.String(title="Vendor Name", description="Vendor company name", example="Jane Doe Inc.", required=True, allow_none=False)
    vat = fields.String(title="Vendor VAT", description="Vendor VAT number", example="12345678912", required=True, allow_none=False)
    email = fields.String(title="Vendor Email", description="Email address of related vendor", example="test@example.com", required=True, allow_none=False)
    mobile = fields.String(title="Vendor Mobile", description="Mobile phone number of related vendor", example="+905001234567", required=True, allow_none=False)
    ref = fields.String(required=False, title="Vendor Reference Number", description="Vendor Reference", example="ABC01", allow_none=False)
    amount = fields.Float(title="Amount", description="Amount to pay", example=1200.0, required=True, allow_none=False)
    description = fields.String(required=False, title="Payment Description", description="Description about related payment item", example="ABC01", allow_none=False)


class VendorPaymentCreate(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.create"
    _inherit = "payment.credential.hash"

    payments = fields.List(NestedModel("vendor.payment.item"), title="Payment List", description="List of payment items", required=True, allow_none=False)


class VendorPaymentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.output"
    _inherit = "payment.output"


class VendorPaymentItemWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.payment.item.webhook"
    _inherit = "system.payment.item.webhook"
