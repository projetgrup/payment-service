# -*- coding: utf-8 -*-
from odoo import _lt
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PaymentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.output"

    status = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Response Code"), "description": _lt("Integer which is returned to represent response"), "example": 0})
    message = fields.String(required=True, allow_none=False, metadata={"title": _lt("Response Message"), "description": _lt("Description which is returned to represent response"), "example": "Success"})


class PaymentCredentialApikey(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential.apikey"

    apikey = fields.String(required=True, allow_none=False, metadata={"title": _lt("Application Key"), "description": _lt("API Key which is acquired by your service provider"), "example": "1x2cdaa3-35df-2eff-aeq2-5d74387701xd"})


class PaymentCredentialSecretkey(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential.secretkey"
    _inherit = "payment.credential.apikey"

    secretkey = fields.String(required=True, allow_none=False, metadata={"title": _lt("Secret Key"), "description": _lt("Secret Key which is given to you by your service provider"), "example": "xa18a2325z80c73ay871au54ba169c76"})


class PaymentCredentialHash(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential.hash"
    _inherit = "payment.credential.apikey"

    hash = fields.String(required=True, allow_none=False, metadata={"title": _lt("Hash Data"), "description": _lt("Calculated as the following: 'BASE64_ENCODE(SHA_256(APPLICATION_KEY + SECRET_KEY + ID))'. ID must be unique, but if you don't know what to do, just use 0 for it"), "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})


class PaymentCredentialToken(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential.token"
    _inherit = "payment.credential.apikey"

    token = fields.String(required=True, allow_none=False, metadata={"title": _lt("Payment Token"), "description": _lt("UUID which is generated especially for credit card payments"), "example": "15a8ecc1-731c-411b-89fd-283e1c55cfaf"})


class PaymentRefundInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.refund.input"
    _inherit = "payment.credential.hash"

    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Refund Amount"), "description": _lt("Amount to refund"), "example": 10.71})


class PaymentCredential(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential"

    apikey = fields.String(required=True, allow_none=False, metadata={"title": _lt("Application Key"), "description": _lt("API Key which is acquired by your service provider"), "example": "1x2cdaa3-35df-2eff-aeq2-5d74387701xd"})
    secretkey = fields.String(required=False, allow_none=False, metadata={"title": _lt("Secret Key"), "description": _lt("Secret Key which is given to you by your service provider"), "example": "xa18a2325z80c73ay871au54ba169c76"})
    hash = fields.String(required=False, allow_none=False, metadata={"title": _lt("Hash Data"), "description": _lt("Calculated as the following: BASE64_ENCODE(SHA_256(APPLICATION_KEY + SECRET_KEY + ID))"), "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})
    token = fields.String(required=False, allow_none=False, metadata={"title": _lt("Payment Token"), "description": _lt("UUID which is generated especially for credit card payments"), "example": "15a8ecc1-731c-411b-89fd-283e1c55cfaf"})


class PaymentPartner(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.partner"

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


class PaymentProduct(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.product"

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Product Name"), "description": _lt("Product name"), "example": "Maintenance Services"})


class PaymentCard(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.card"

    name = fields.String(metadata={"title": _lt("Credit Card Holder Name"), "description": _lt("Name field which is placed on front side of the card"), "example": "John Doe"})
    number = fields.String(metadata={"title": _lt("Credit Card Number"), "description": _lt("Masked number of related credit card"), "example": "123478******1234"})
    type = fields.String(metadata={"title": _lt("Credit Card Type"), "description": "Visa, MasterCard, Amex, Troy...", "example": "Troy"})
    family = fields.String(metadata={"title": _lt("Credit Card Family"), "description": "Bonus, Maximum, Axess, Bankkart...", "example": "Paraf"})


class PaymentOrder(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.order"

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Order Name"), "description": _lt("Order name"), "example": "S123564"})
    products = fields.List(NestedModel("payment.product"), required=False, metadata={"title": _lt("Products List"), "description": _lt("List of related products")})


class PaymentUrlMethod(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.url.method"

    result = fields.String(required=True, allow_none=False, metadata={"title": _lt("Return URL"), "description": _lt("Return URL when user picks card payment method"), "example": "https://example.com/method/result"})
    webhook = fields.String(required=False, allow_none=False, metadata={"title": _lt("Webhook URL"), "description": _lt("Webhook URL to send a notification"), "example": "https://example.com/method/webhook"})


class PaymentUrl(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.url"

    card = NestedModel("payment.url.method", required=True, metadata={"title": _lt("Return URLs by card payment method"), "description": _lt("URL addresses when card payment is selected")})
    bank = NestedModel("payment.url.method", required=False, metadata={"title": _lt("Return URLs by bank payment method"), "description": _lt("URL addresses when bank payment is selected")})


class PaymentPrepareInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.input"
    _inherit = "payment.credential.hash"

    id = fields.Integer(required=True, allow_none=False, metadata={"title": "ID", "description": _lt("Any unique number related to your specified record in your database for tracking the payment flow"), "example": 12})
    expiration = fields.DateTime(allow_none=False, metadata={"title": _lt("Expiration Date"), "description": _lt("Datetime in ISO format to get transaction expired"), "example": "2023-01-01T00:00:00"})
    campaign = fields.String(metadata={"title": _lt("Campaign Name"), "description": _lt("Name of campaign to be used in getting installment options"), "example": "Standard"})
    partner = NestedModel("payment.partner", required=True, metadata={"title": _lt("Partner information related to request"), "description": _lt("Partner information")})
    order = NestedModel("payment.order", required=True, metadata={"title": _lt("Order information related to request"), "description": _lt("Order details")})
    url = NestedModel("payment.url", required=True, metadata={"title": _lt("Return URLs by payment method"), "description": _lt("URL addresses")})
    html = fields.String(metadata={"title": _lt("Custom HTML"), "description": _lt("Custom code to be viewed bottom of the page"), "example": "<p>Copyright</p>"})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Amount"), "description": _lt("Amount to pay"), "example": 145.3})
    methods = fields.List(fields.String(), required=False, allow_none=False, metadata={"title": _lt("Method List"), "description": _lt("List of codes of methods. Possible values are 'card' and 'bank'."), "example": ["bank", "card"]})


class PaymentPrepareOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.output"
    _inherit = "payment.output"

    hash = fields.String(required=False, allow_none=False, metadata={"title": _lt("Hash Data"), "description": _lt("Encrypted data to check if hash is created successfully"), "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})


class PaymentInstallment(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.installment"

    amount = fields.Float(metadata={"title": _lt("Installment Amount"), "description": _lt("Monthly payment amount"), "example": 18.16})
    count = fields.Integer(metadata={"title": _lt("Installment Count"), "description": _lt("Total applied installment count if exist"), "example": 8})
    description = fields.String(metadata={"title": _lt("Installment Description"), "description": _lt("Statement describing how installement count is formed"), "example": "6+2 (+2 Campaign)"})


class PaymentCommissionCost(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.commission.cost"


    rate = fields.Float(metadata={"title": _lt("Cost Commision Rate"), "description": _lt("Percentage which is subtracted from total payment amount"), "example": 1.5})
    amount = fields.Float(metadata={"title": _lt("Cost Commision Amount"), "description": _lt("Amount which is subtracted from total payment amount"), "example": 2.18})


class PaymentCommissionCustomer(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.commission.customer"

    rate = fields.Float(metadata={"title": _lt("Customer Commision Rate"), "description": _lt("Percentage which is to be paid as commission by your customer"), "example": 3})
    amount = fields.Float(metadata={"title": _lt("Customer Commision Amount"), "description": _lt("Amount which is to be paid as commission by your customer"), "example": 4.36})


class PaymentCommission(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.commission"

    cost = NestedModel("payment.commission.cost", metadata={"title": _lt("Cost commission information"), "description": _lt("Cost commission details")})
    customer = NestedModel("payment.commission.customer", metadata={"title": _lt("Customer commission information"), "description": _lt("Customer commission details")})


class PaymentAmount(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.amount"

    amount = fields.Float(metadata={"title": _lt("Payment Amount"), "description": _lt("Total amount of payment"), "example": 145.3})
    raw = fields.Float(metadata={"title": _lt("Payment Raw Amount"), "description": _lt("Total amount of payment without customer commission rate"), "example": 140.94})
    fees = fields.Float(metadata={"title": _lt("Payment Fee"), "description": _lt("System use charge"), "example": 10})
    installment = NestedModel("payment.installment", metadata={"title": _lt("Installment information related to transaction"), "description": _lt("Installment details")})
    installment = NestedModel("payment.installment", metadata={"title": _lt("Installment information related to transaction"), "description": _lt("Installment details")})
    commission = NestedModel("payment.commission", metadata={"title": _lt("Commission information related to transaction"), "description": _lt("Commission details")})


class PaymentTransactionPartner(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.transaction.partner"

    name = fields.String(metadata={"title": _lt("Partner Name"), "description": _lt("Partner name"), "example": "John Doe"})
    ip_address = fields.String(metadata={"title": _lt("IP Address"), "description": _lt("Address linked to transaction owner"), "example": "34.06.50.01"})


class PaymentTransaction(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.transaction"

    state = fields.String(metadata={"title": _lt("Payment State"), "description": _lt("State of payment, which indicates whether if payment is successful or not"), "example": "done"})
    provider = fields.String(metadata={"title": _lt("Provider Code"), "description": _lt("Codename of payment acquirer"), "example": "card"})
    virtual_pos_name = fields.String(metadata={"title": _lt("Virtual PoS Name"), "description": _lt("PoS name you assigned to track payment flow"), "example": "My PoS | Long Term"})
    order_id = fields.String(metadata={"title": _lt("Payment Token"), "description": _lt("UUID which is generated especially for credit card payments"), "example": "15a8ecc1-731c-411b-89fd-283e1c55cfaf"})
    transaction_id = fields.String(metadata={"title": _lt("Payment TransactionID"), "description": _lt("Special value which is generated especially for credit card payments"), "example": "v3a2a10684j94ue0151z7f2e9bbdvd0p"})
    message = fields.String(metadata={"title": _lt("State Message"), "description": _lt("Description of payment transaction"), "example": "Transaction is successful"})
    partner = NestedModel("payment.transaction.partner", metadata={"title": _lt("Partner related to transaction"), "description": _lt("Partner details")})
    card = NestedModel("payment.card", metadata={"title": _lt("Credit card information related to transaction"), "description": _lt("Credit card details")})
    amounts = NestedModel("payment.amount", metadata={"title": _lt("Amounts related to transaction"), "description": _lt("Amount details")})


class PaymentResultOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.result.output"
    _inherit = "payment.output"

    transaction = NestedModel("payment.transaction", metadata={"title": _lt("Transaction information related to request"), "description": _lt("Transaction details")})


class PaymentResultWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.result.webhook"
    _inherit = "payment.result.output"


class PaymentStatusOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.status.output"
    _inherit = "payment.output"

    date = fields.String(required=False, allow_none=False, metadata={"title": _lt("Payment Date"), "description": _lt("Transaction date and time"), "example": "19-10-2020 08:02:36"})
    name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Payment Name"), "description": _lt("Reference name of payment"), "example": "JET/2020/5648"})
    successful = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Payment Successful"), "description": _lt("True if payment is successful"), "example": True})
    completed = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Payment Completed"), "description": _lt("True if payment is completed"), "example": True})
    cancelled = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Payment Cancelled"), "description": _lt("True if payment is cancelled"), "example": False})
    refunded = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Payment Refunded"), "description": _lt("True if payment is refunded"), "example": False})
    threed = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Payment with 3D Secure"), "description": _lt("True if transaction is done through 3D Secure process"), "example": True})
    amount = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Payment Amount"), "description": _lt("Total amount of payment"), "example": 145.3})
    commission_rate = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Cost Commision Rate"), "description": _lt("Percentage which is subtracted from total payment amount"), "example": 1.5})
    commission_amount = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Cost Commision Amount"), "description": _lt("Amount which is subtracted from total payment amount"), "example": 2.18})
    customer_rate = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Customer Commision Rate"), "description": _lt("Percentage which is to be paid as commission by your customer"), "example": 3})
    customer_amount = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Customer Commision Amount"), "description": _lt("Amount which is to be paid as commission by your customer"), "example": 4.36})
    currency = fields.String(required=False, allow_none=False, metadata={"title": _lt("Payment Currency"), "description": _lt("Currency which is used in related payment transaction"), "example": "TRY"})
    auth_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("Authorization Code"), "description": _lt("Code given by service provider"), "example": ""})
    service_ref_id = fields.String(required=False, allow_none=False, metadata={"title": _lt("Service ReferenceID"), "description": _lt("Reference number given by service provider"), "example": ""})
