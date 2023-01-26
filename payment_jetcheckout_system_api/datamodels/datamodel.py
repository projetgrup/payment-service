# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class SystemPaymentItemParent(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.parent"

    name = fields.String(title="Parent Name", description="Parent name and surname", example="Jane Doe", required=True)
    vat = fields.String(title="Parent VAT", description="Parent citizen number", example="12345678912", required=True)


class SystemPaymentItemChild(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.child"

    name = fields.String(title="Child Name", description="Child name and surname", example="John Doe", required=True)
    vat = fields.String(title="Child VAT", description="Child citizen number", example="12345678912", required=True)
    reference = fields.String(title="Child Reference", description="Child reference details", example="CODE12", required=True)


class SystemPaymentItemAmountDiscount(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.amount.discount"

    prepayment = fields.Float(title="Prepayment Discount Amount", description="Prepayment discount amount of payment item", example=80.0, required=True)


class SystemPaymentItemAmountInstallment(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.amount.installment"

    count = fields.Integer(title="Installment Count", description="Installment count of payment item", example=5, required=True)
    amount = fields.Float(title="Installment Amount", description="Installment amount of payment item", example=400.0, required=True)


class SystemPaymentItemAmount(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.amount"

    total = fields.Float(title="Total Amount", description="Total amount to be paid", example=2200.0, required=True)
    discount = NestedModel("system.payment.item.amount.discount", title="Discount details of payment transaction", description="Discount information", required=True)
    installment = NestedModel("system.payment.item.amount.installment", title="Installment details of payment transaction", description="Installment information", required=True)
    paid = fields.Float(title="Payment Amount", description="Paid amount for current payment transaction", example=2000.0, required=True)


class SystemPaymentItem(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item"

    amount = NestedModel("system.payment.item.amount", title="Amount Information", description="Amount details of payment transaction", required=True)


class SystemPaymentCard(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.card"

    family = fields.String(title="Credit Card Family", description="Card family name of credit card related to transaction", example="Paraf", required=True)
    vpos = fields.String(title="Virtual PoS Name", description="Virtual pos name which is registered to payment system", example="General", required=True)


class SystemPaymentItemWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "system.payment.item.webhook"

    parent = NestedModel("system.payment.item.parent", title="Parent Information", description="Parent information of payment item", required=True)
    items = fields.List(NestedModel("system.payment.item"), title="Payment Information", description="Payment item details which contains amounts and other informations", required=True)
    card = NestedModel("system.payment.card", title="Card Information", description="Credit card information which are used in payment", required=True)
