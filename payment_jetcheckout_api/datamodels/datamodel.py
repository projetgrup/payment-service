# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel


class PaymentResponse(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.response"

    response_code = fields.Integer(required=True, allow_none=False, title="Response Code", description="Integer which is returned to represent response", example=0)
    response_message = fields.String(required=True, allow_none=False, title="Response Message", description="Description which is returned to represent response", example="Success")


class PaymentApi(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.api"

    application_key = fields.String(required=True, allow_none=False, title="Application Key", description="API Key which is acquired by your service provider", example="1x2cdaa3-35df-2eff-aeq2-5d74387701xd")


class PaymentApiSecret(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.api.secret"
    _inherit = "payment.api"

    secret_key = fields.String(required=True, allow_none=False, title="Secret Key", description="Secret Key which is given to you by your service provider", example="xa18a2325z80c73ay871au54ba169c76")


class PaymentHashInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.hash.input"
    _inherit = "payment.api"

    hash = fields.String(required=True, allow_none=False, title="Hash Data", description="Calculated as the following: BASE64_ENCODE(SHA_256(APPLICATION_KEY + SECRET_KEY + ID))", example="LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto=")


class PaymentTokenInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.token.input"
    _inherit = "payment.api"

    token = fields.String(required=True, allow_none=False, title="Payment Token", description="UUID which is generated especially for credit card payments", example="15a8ecc1-731c-411b-89fd-283e1c55cfaf")


class PaymentRefundInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.refund.input"
    _inherit = "payment.token.input"

    amount = fields.Float(required=True, allow_none=False, title="Refund Amount", description="Amount to refund", example=10.71)


class PaymentPrepareInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.input"
    _inherit = "payment.hash.input"

    id = fields.Integer(required=True, allow_none=False, title="ID", description="Any unique number related to your specified record in your database for tracking the payment flow", example=12)
    amount = fields.Float(required=True, allow_none=False, title="Amount", description="Amount to pay", example=145.30)
    partner = fields.Dict(required=True, allow_none=False, title="Partner", description="Partner Name", example="John Doe")
    order = fields.Dict(required=True, allow_none=False, title="Order", description="Order Name", example="S123564")
    product = fields.Dict(required=True, allow_none=False, title="Product", description="Product Name", example="Maintenance Services")
    card_return_url = fields.String(required=True, allow_none=False, title="Card Return URL", description="Return URL when user picks card payment method", example="https://example.com/card/result")
    bank_return_url = fields.String(required=True, allow_none=False, title="Bank Return URL", description="Return URL when user picks bank payment method", example="https://example.com/bank/result")
    bank_webhook_url = fields.String(required=True, allow_none=False, title="Bank Webhook URL", description="Webhook URL to send a notification to your system when user choose to pay with bank transfer", example="https://example.com/bank/webhook")


class PaymentPrepareOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.output"
    _inherit = "payment.response"

    hash = fields.String(required=False, allow_none=False, title="Hash Data", description="Encrypted data to check if hash is created successfully", example="LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto=")


class PaymentResultOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.result.output"
    _inherit = "payment.response"

    provider = fields.String(required=False, allow_none=False, title="Provider Code", description="Codename of payment acquirer", example="card")
    state = fields.String(required=False, allow_none=False, title="Payment State", description="State of payment, which indicates whether if payment is successful or not", example="done")
    message = fields.String(required=False, allow_none=False, title="State Message", description="Description of payment transaction", example="Payment is successful")
    ip_address = fields.String(required=False, allow_none=False, title="IP Address", description="Address linked to transaction owner", example="127.0.0.1")
    card_name = fields.String(required=False, allow_none=False, title="Credit Card Holder Name", description="Name field which is placed on front side of the card", example="John Doe")
    card_number = fields.String(required=False, allow_none=False, title="Credit Card Number", description="Masked number of related credit card", example="123478******1234")
    card_type = fields.String(required=False, allow_none=False, title="Credit Card Type", description="Visa, MasterCard, Amex, Troy...", example="Troy")
    card_family = fields.String(required=False, allow_none=False, title="Credit Card Family", description="Bonus, Maximum, Axess, Bankkart...", example="Paraf")
    vpos_name = fields.String(required=False, allow_none=False, title="Virtual PoS Name", description="PoS name you assigned to track payment flow", example="My PoS | Long Term")
    order_id = fields.String(required=False, allow_none=False, title="Payment Token", description="UUID which is generated especially for credit card payments", example="15a8ecc1-731c-411b-89fd-283e1c55cfaf")
    transaction_id = fields.String(required=False, allow_none=False, title="Payment TransactionID", description="Special value which is generated especially for credit card payments", example="v3a2a10684j94ue0151z7f2e9bbdvd0p")
    payment_amount = fields.Float(required=False, allow_none=False, title="Payment Amount", description="Total amount of payment", example=145.30)
    fees = fields.Float(required=False, allow_none=False, title="Payment Fee", description="System use charge", example=10)
    installment_count = fields.Integer(required=False, allow_none=False, title="Installment Count", description="Total applied installment count if exist", example=8)
    installment_desc = fields.String(required=False, allow_none=False, title="Installment Description", description="Statement describing how installement count is formed", example="6+2 (+2 Campaign)")
    installment_amount = fields.Float(required=False, allow_none=False, title="Installment Amount", description="Monthly payment amount", example=18.16)
    commission_rate = fields.Float(required=False, allow_none=False, title="Cost Commision Rate", description="Percentage which is subtracted from total payment amount", example=1.5)
    commission_amount = fields.Float(required=False, allow_none=False, title="Cost Commision Amount", description="Amount which is subtracted from total payment amount", example=2.18)
    customer_rate = fields.Float(required=False, allow_none=False, title="Customer Commision Rate", description="Percentage which is to be paid as commission by your customer", example=3)
    customer_amount = fields.Float(required=False, allow_none=False, title="Customer Commision Amount", description="Amount which is to be paid as commission by your customer", example=4.36)


class PaymentStatusOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.status.output"
    _inherit = "payment.response"

    date = fields.String(required=False, allow_none=False, title="Payment Date", description="Transaction date and time", example="19-10-2020 08:02:36")
    name = fields.String(required=False, allow_none=False, title="Payment Name", description="Reference name of payment", example="JET/2020/5648")
    successful = fields.Boolean(required=False, allow_none=False, title="Payment Successful", description="True if payment is successful", example=True)
    completed = fields.Boolean(required=False, allow_none=False, title="Payment Completed", description="True if payment is completed", example=True)
    cancelled = fields.Boolean(required=False, allow_none=False, title="Payment Cancelled", description="True if payment is cancelled", example=False)
    refunded = fields.Boolean(required=False, allow_none=False, title="Payment Refunded", description="True if payment is refunded", example=False)
    threed = fields.Boolean(required=False, allow_none=False, title="Payment with 3D Secure", description="True if transaction is done through 3D Secure process", example=True)
    amount = fields.Float(required=False, allow_none=False, title="Payment Amount", description="Total amount of payment", example=145.30)
    commission_rate = fields.Float(required=False, allow_none=False, title="Cost Commision Rate", description="Percentage which is subtracted from total payment amount", example=1.5)
    commission_amount = fields.Float(required=False, allow_none=False, title="Cost Commision Amount", description="Amount which is subtracted from total payment amount", example=2.18)
    customer_rate = fields.Float(required=False, allow_none=False, title="Customer Commision Rate", description="Percentage which is to be paid as commission by your customer", example=3)
    customer_amount = fields.Float(required=False, allow_none=False, title="Customer Commision Amount", description="Amount which is to be paid as commission by your customer", example=4.36)
    currency = fields.String(required=False, allow_none=False, title="Payment Currency", description="Currency which is used in related payment transaction", example="TRY")
    auth_code = fields.String(required=False, allow_none=False, title="Authorization Code", description="Code given by service provider", example="")
    service_ref_id = fields.String(required=False, allow_none=False, title="Service ReferenceID", description="Reference number given by service provider", example="")
