# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PaymentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.output"

    status = fields.Integer(required=True, allow_none=False, metadata={"title": "Response Code", "description": "Integer which is returned to represent response", "example": 0})
    message = fields.String(required=True, allow_none=False, metadata={"title": "Response Message", "description": "Description which is returned to represent response", "example": "Success"})


class PaymentCredentialApikey(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential.apikey"

    apikey = fields.String(required=True, allow_none=False, metadata={"title": "Application Key", "description": "API Key which is acquired by your service provider", "example": "1x2cdaa3-35df-2eff-aeq2-5d74387701xd"})


class PaymentCredentialSecretkey(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential.secretkey"
    _inherit = "payment.credential.apikey"

    secretkey = fields.String(required=True, allow_none=False, metadata={"title": "Secret Key", "description": "Secret Key which is given to you by your service provider", "example": "xa18a2325z80c73ay871au54ba169c76"})


class PaymentCredentialHash(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential.hash"
    _inherit = "payment.credential.apikey"

    hash = fields.String(required=True, allow_none=False, metadata={"title": "Hash Data", "description": "Calculated as the following: 'BASE64_ENCODE(SHA_256(APPLICATION_KEY + SECRET_KEY + ID))'. ID must be unique, but if you don't know what to do, just use 0 for it", "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})


class PaymentCredentialToken(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential.token"
    _inherit = "payment.credential.apikey"

    token = fields.String(required=True, allow_none=False, metadata={"title": "Payment Token", "description": "UUID which is generated especially for credit card payments", "example": "15a8ecc1-731c-411b-89fd-283e1c55cfaf"})


class PaymentRefundInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.refund.input"
    _inherit = "payment.credential.hash"

    amount = fields.Float(required=True, allow_none=False, metadata={"title": "Refund Amount", "description": "Amount to refund", "example": 10.71})


class PaymentCredential(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credential"

    apikey = fields.String(required=True, allow_none=False, metadata={"title": "Application Key", "description": "API Key which is acquired by your service provider", "example": "1x2cdaa3-35df-2eff-aeq2-5d74387701xd"})
    secretkey = fields.String(required=False, allow_none=False, metadata={"title": "Secret Key", "description": "Secret Key which is given to you by your service provider", "example": "xa18a2325z80c73ay871au54ba169c76"})
    hash = fields.String(required=False, allow_none=False, metadata={"title": "Hash Data", "description": "Calculated as the following: BASE64_ENCODE(SHA_256(APPLICATION_KEY + SECRET_KEY + ID))", "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})
    token = fields.String(required=False, allow_none=False, metadata={"title": "Payment Token", "description": "UUID which is generated especially for credit card payments", "example": "15a8ecc1-731c-411b-89fd-283e1c55cfaf"})


class PaymentPartner(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.partner"

    name = fields.String(required=True, allow_none=False, metadata={"title": "Partner Name", "description": "Partner name", "example": "John Doe"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": "Partner VAT", "description": "Partner VAT number", "example": "12345678910"})
    email = fields.String(required=True, allow_none=False, metadata={"title": "Email Address", "description": "Email address", "example": "test@example.com"})
    phone = fields.String(required=True, allow_none=False, metadata={"title": "Phone Number", "description": "Phone number", "example": "+905321234567"})
    ip_address = fields.String(required=True, allow_none=False, metadata={"title": "IP Address", "description": "IP Address", "example": "34.06.50.01"})
    country = fields.String(required=False, allow_none=False, metadata={"title": "Country Code", "description": "Country code", "example": "TR"})
    state = fields.String(required=False, allow_none=False, metadata={"title": "State Code", "description": "State code", "example": "34"})
    city = fields.String(required=False, allow_none=True, metadata={"title": "City/Town Name", "description": "City/Town name", "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=False, metadata={"title": "Partner Address", "description": "Partner address", "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=True, metadata={"title": "ZIP Code", "description": "ZIP Code", "example": "34100"})
    contact = fields.String(required=False, allow_none=False, metadata={"title": "Contact Name", "description": "Contact name", "example": "Jane Doe"})


class PaymentProduct(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.product"

    name = fields.String(required=True, allow_none=False, metadata={"title": "Product Name", "description": "Product name", "example": "Maintenance Services"})


class PaymentCard(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.card"

    name = fields.String(metadata={"title": "Credit Card Holder Name", "description": "Name field which is placed on front side of the card", "example": "John Doe"})
    number = fields.String(metadata={"title": "Credit Card Number", "description": "Masked number of related credit card", "example": "123478******1234"})
    type = fields.String(metadata={"title": "Credit Card Type", "description": "Visa, MasterCard, Amex, Troy...", "example": "Troy"})
    family = fields.String(metadata={"title": "Credit Card Family", "description": "Bonus, Maximum, Axess, Bankkart...", "example": "Paraf"})


class PaymentOrder(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.order"

    name = fields.String(required=True, allow_none=False, metadata={"title": "Order Name", "description": "Order name", "example": "S123564"})
    products = fields.List(NestedModel("payment.product"), required=False, metadata={"title": "Products List", "description": "List of related products"})


class PaymentUrlMethod(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.url.method"

    result = fields.String(required=True, allow_none=False, metadata={"title": "Return URL", "description": "Return URL when user picks card payment method", "example": "https://example.com/method/result"})
    webhook = fields.String(required=False, allow_none=False, metadata={"title": "Webhook URL", "description": "Webhook URL to send a notification", "example": "https://example.com/method/webhook"})


class PaymentUrl(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.url"

    card = NestedModel("payment.url.method", required=True, metadata={"title": "Return URLs by card payment method", "description": "URL addresses when card payment is selected"})
    bank = NestedModel("payment.url.method", required=False, metadata={"title": "Return URLs by bank payment method", "description": "URL addresses when bank payment is selected"})


class PaymentPrepareInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.input"
    _inherit = "payment.credential.hash"

    id = fields.Integer(required=True, allow_none=False, metadata={"title": "ID", "description": "Any unique number related to your specified record in your database for tracking the payment flow", "example": 12})
    expiration = fields.DateTime(allow_none=False, metadata={"title": "Expiration Date", "description": "Datetime in ISO format to get transaction expired", "example": "2023-01-01T00:00:00"})
    campaign = fields.String(metadata={"title": "Campaign Name", "description": "Name of campaign to be used in getting installment options", "example": "Standard"})
    partner = NestedModel("payment.partner", required=True, metadata={"title": "Partner information related to request", "description": "Partner information"})
    order = NestedModel("payment.order", required=True, metadata={"title": "Order information related to request", "description": "Order details"})
    url = NestedModel("payment.url", required=True, metadata={"title": "Return URLs by payment method", "description": "URL addresses"})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": "Amount", "description": "Amount to pay", "example": 145.3})
    methods = fields.List(fields.String(), required=False, allow_none=False, metadata={"title": "Method List", "description": "List of codes of methods. Possible values are 'card' and 'bank'.", "example": ["bank", "card"]})


class PaymentPrepareOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.output"
    _inherit = "payment.output"

    hash = fields.String(required=False, allow_none=False, metadata={"title": "Hash Data", "description": "Encrypted data to check if hash is created successfully", "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})


class PaymentInstallment(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.installment"

    amount = fields.Float(metadata={"title": "Installment Amount", "description": "Monthly payment amount", "example": 18.16})
    count = fields.Integer(metadata={"title": "Installment Count", "description": "Total applied installment count if exist", "example": 8})
    description = fields.String(metadata={"title": "Installment Description", "description": "Statement describing how installement count is formed", "example": "6+2 (+2 Campaign)"})


class PaymentCommissionCost(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.commission.cost"


    rate = fields.Float(metadata={"title": "Cost Commision Rate", "description": "Percentage which is subtracted from total payment amount", "example": 1.5})
    amount = fields.Float(metadata={"title": "Cost Commision Amount", "description": "Amount which is subtracted from total payment amount", "example": 2.18})


class PaymentCommissionCustomer(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.commission.customer"

    rate = fields.Float(metadata={"title": "Customer Commision Rate", "description": "Percentage which is to be paid as commission by your customer", "example": 3})
    amount = fields.Float(metadata={"title": "Customer Commision Amount", "description": "Amount which is to be paid as commission by your customer", "example": 4.36})


class PaymentCommission(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.commission"

    cost = NestedModel("payment.commission.cost", metadata={"title": "Cost commission information", "description": "Cost commission details"})
    customer = NestedModel("payment.commission.customer", metadata={"title": "Customer commission information", "description": "Customer commission details"})


class PaymentAmount(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.amount"

    amount = fields.Float(metadata={"title": "Payment Amount", "description": "Total amount of payment", "example": 145.3})
    fees = fields.Float(metadata={"title": "Payment Fee", "description": "System use charge", "example": 10})
    installment = NestedModel("payment.installment", metadata={"title": "Installment information related to transaction", "description": "Installment details"})
    installment = NestedModel("payment.installment", metadata={"title": "Installment information related to transaction", "description": "Installment details"})
    commission = NestedModel("payment.commission", metadata={"title": "Commission information related to transaction", "description": "Commission details"})


class PaymentTransactionPartner(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.transaction.partner"

    name = fields.String(metadata={"title": "Partner Name", "description": "Partner name", "example": "John Doe"})
    ip_address = fields.String(metadata={"title": "IP Address", "description": "Address linked to transaction owner", "example": "34.06.50.01"})


class PaymentTransaction(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.transaction"

    state = fields.String(metadata={"title": "Payment State", "description": "State of payment, which indicates whether if payment is successful or not", "example": "done"})
    provider = fields.String(metadata={"title": "Provider Code", "description": "Codename of payment acquirer", "example": "card"})
    virtual_pos_name = fields.String(metadata={"title": "Virtual PoS Name", "description": "PoS name you assigned to track payment flow", "example": "My PoS | Long Term"})
    order_id = fields.String(metadata={"title": "Payment Token", "description": "UUID which is generated especially for credit card payments", "example": "15a8ecc1-731c-411b-89fd-283e1c55cfaf"})
    transaction_id = fields.String(metadata={"title": "Payment TransactionID", "description": "Special value which is generated especially for credit card payments", "example": "v3a2a10684j94ue0151z7f2e9bbdvd0p"})
    message = fields.String(metadata={"title": "State Message", "description": "Description of payment transaction", "example": "Transaction is successful"})
    partner = NestedModel("payment.transaction.partner", metadata={"title": "Partner related to transaction", "description": "Partner details"})
    card = NestedModel("payment.card", metadata={"title": "Credit card information related to transaction", "description": "Credit card details"})
    amounts = NestedModel("payment.amount", metadata={"title": "Amounts related to transaction", "description": "Amount details"})


class PaymentResultOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.result.output"
    _inherit = "payment.output"

    transaction = NestedModel("payment.transaction", metadata={"title": "Transaction information related to request", "description": "Transaction details"})


class PaymentStatusOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.status.output"
    _inherit = "payment.output"

    date = fields.String(required=False, allow_none=False, metadata={"title": "Payment Date", "description": "Transaction date and time", "example": "19-10-2020 08:02:36"})
    name = fields.String(required=False, allow_none=False, metadata={"title": "Payment Name", "description": "Reference name of payment", "example": "JET/2020/5648"})
    successful = fields.Boolean(required=False, allow_none=False, metadata={"title": "Payment Successful", "description": "True if payment is successful", "example": True})
    completed = fields.Boolean(required=False, allow_none=False, metadata={"title": "Payment Completed", "description": "True if payment is completed", "example": True})
    cancelled = fields.Boolean(required=False, allow_none=False, metadata={"title": "Payment Cancelled", "description": "True if payment is cancelled", "example": False})
    refunded = fields.Boolean(required=False, allow_none=False, metadata={"title": "Payment Refunded", "description": "True if payment is refunded", "example": False})
    threed = fields.Boolean(required=False, allow_none=False, metadata={"title": "Payment with 3D Secure", "description": "True if transaction is done through 3D Secure process", "example": True})
    amount = fields.Float(required=False, allow_none=False, metadata={"title": "Payment Amount", "description": "Total amount of payment", "example": 145.3})
    commission_rate = fields.Float(required=False, allow_none=False, metadata={"title": "Cost Commision Rate", "description": "Percentage which is subtracted from total payment amount", "example": 1.5})
    commission_amount = fields.Float(required=False, allow_none=False, metadata={"title": "Cost Commision Amount", "description": "Amount which is subtracted from total payment amount", "example": 2.18})
    customer_rate = fields.Float(required=False, allow_none=False, metadata={"title": "Customer Commision Rate", "description": "Percentage which is to be paid as commission by your customer", "example": 3})
    customer_amount = fields.Float(required=False, allow_none=False, metadata={"title": "Customer Commision Amount", "description": "Amount which is to be paid as commission by your customer", "example": 4.36})
    currency = fields.String(required=False, allow_none=False, metadata={"title": "Payment Currency", "description": "Currency which is used in related payment transaction", "example": "TRY"})
    auth_code = fields.String(required=False, allow_none=False, metadata={"title": "Authorization Code", "description": "Code given by service provider", "example": ""})
    service_ref_id = fields.String(required=False, allow_none=False, metadata={"title": "Service ReferenceID", "description": "Reference number given by service provider", "example": ""})
