# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class SystemPaymentItemParent(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.parent"

    name = fields.String(required=True, metadata={"title": "Parent Name", "description": "Parent name and surname", "example": "Jane Doe"})
    vat = fields.String(required=True, metadata={"title": "Parent VAT", "description": "Parent citizen number", "example": "12345678912"})


class SystemPaymentItemChild(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.child"

    name = fields.String(required=True, metadata={"title": "Child Name", "description": "Child name and surname", "example": "John Doe"})
    vat = fields.String(required=True, metadata={"title": "Child VAT", "description": "Child citizen number", "example": "12345678912"})
    reference = fields.String(required=True, metadata={"title": "Child Reference", "description": "Child reference details", "example": "CODE12"})


class SystemPaymentItemAmountDiscount(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.amount.discount"

    prepayment = fields.Float(required=True, metadata={"title": "Prepayment Discount Amount", "description": "Prepayment discount amount of payment item", "example": 80.0})


class SystemPaymentItemAmountInstallment(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.amount.installment"

    count = fields.Integer(required=True, metadata={"title": "Installment Count", "description": "Installment count of payment item", "example": 5})
    amount = fields.Float(required=True, metadata={"title": "Installment Amount", "description": "Installment amount of payment item", "example": 400.0})


class SystemPaymentItemAmount(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.amount"

    total = fields.Float(required=True, metadata={"title": "Total Amount", "description": "Total amount to be paid", "example": 2200.0})
    discount = NestedModel("system.payment.item.amount.discount", required=True, metadata={"title": "Discount details of payment transaction", "description": "Discount information"})
    installment = NestedModel("system.payment.item.amount.installment", required=True, metadata={"title": "Installment details of payment transaction", "description": "Installment information"})
    paid = fields.Float(required=True, metadata={"title": "Payment Amount", "description": "Paid amount for current payment transaction", "example": 2000.0})


class SystemPaymentItem(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item"

    amount = NestedModel("system.payment.item.amount", required=True, metadata={"title": "Amount Information", "description": "Amount details of payment transaction"})


class SystemPaymentCard(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.card"

    family = fields.String(required=True, metadata={"title": "Credit Card Family", "description": "Card family name of credit card related to transaction", "example": "Paraf"})
    vpos = fields.String(required=True, metadata={"title": "Virtual PoS Name", "description": "Virtual pos name which is registered to payment system", "example": "General"})


class SystemPaymentItemWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.webhook"

    parent = NestedModel("system.payment.item.parent", required=True, metadata={"title": "Parent Information", "description": "Parent information of payment item"})
    items = fields.List(NestedModel("system.payment.item"), required=True, metadata={"title": "Payment Information", "description": "Payment item details which contains amounts and other informations"})
    card = NestedModel("system.payment.card", required=True, metadata={"title": "Card Information", "description": "Credit card information which are used in payment"})
