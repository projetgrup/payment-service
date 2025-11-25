# -*- coding: utf-8 -*-
from marshmallow import fields, validate
from odoo import _lt
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

    token = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("Payment Token"), "description": _lt("UUID which is generated especially for credit card payments"), "example": "15a8ecc1-731c-411b-89fd-283e1c55cfaf"})


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


class PaymentPartnerBank(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.partner.bank"

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Account Name"), "description": _lt("Account name"), "example": "Bank Account"})
    iban = fields.String(required=True, allow_none=False, metadata={"title": _lt("Account IBAN"), "description": _lt("Account IBAN"), "example": "TR000000000000000000000000"})


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
    banks = fields.List(NestedModel("payment.partner.bank"), required=False, metadata={"title": _lt("Banks List"), "description": _lt("List of bank accounts of partner")})


class PaymentProduct(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.product"

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Product Name"), "description": _lt("Product name"), "example": "Maintenance Services"})
    code = fields.String(required=True, allow_none=False, metadata={"title": _lt("Product Code"), "description": _lt("Product code"), "example": "MS-123"})
    qty = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Product Quantity"), "description": _lt("Product quantity"), "example": 2.0})
    price = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Unit Price"), "description": _lt("Unit price"), "example": 30.45})
    brand = fields.String(required=False, allow_none=False, metadata={"title": _lt("Product Brand"), "description": _lt("Product brand"), "example": "Brand"})
    categ = fields.String(required=False, allow_none=False, metadata={"title": _lt("Product Category"), "description": _lt("Product category"), "example": "General"})


class PaymentCard(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.card"

    name = fields.String(metadata={"title": _lt("Credit Card Holder Name"), "description": _lt("Name field which is placed on front side of the card"), "example": "John Doe"})
    number = fields.String(metadata={"title": _lt("Credit Card Number"), "description": _lt("Masked number of related credit card"), "example": "123478******1234"})
    type = fields.String(metadata={"title": _lt("Credit Card Type"), "description": "Credit, Debit, Business...", "example": "Credit"})
    program = fields.String(metadata={"title": _lt("Credit Card Program"), "description": "Visa, Mastercard, Troy...", "example": "Troy"})
    family = fields.String(metadata={"title": _lt("Credit Card Family"), "description": "Bonus, Maximum, Axess, Bankkart...", "example": "Paraf"})


class PaymentCredit(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.credit"

    bank = fields.String(metadata={"title": _lt("Bank Code"), "description": _lt("Bank code"), "example": "34"})


class PaymentOrder(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.order"

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Order Name"), "description": _lt("Order name"), "example": "S123564"})
    products = fields.List(NestedModel("payment.product"), required=False, metadata={"title": _lt("Products List"), "description": _lt("List of related products")})


class PaymentPrepareMethodItem(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.method.item"

    #priority = fields.Integer(required=False, allow_none=False, metadata={"title": _lt("Priority"), "description": _lt("Payment method priority"), "example": 1})
    redirect = fields.String(required=True, allow_none=False, metadata={"title": _lt("Redirect URL"), "description": _lt("Redirect URL when user picks suitable payment method"), "example": "https://example.com/method/result"})
    webhook = fields.String(required=False, allow_none=False, metadata={"title": _lt("Webhook URL"), "description": _lt("Webhook URL to send a notification"), "example": "https://example.com/method/webhook"})


class PaymentPrepareMethodPhysicalPos(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.method.physicalPos"

    ids = fields.List(fields.String, required=True, allow_none=False, validate=validate.NoneOf([[]]), metadata={"title": _lt("PoS IDs"), "description": _lt("List of PoS ID numbers"), "example": ["POS708090"]})
    redirect = fields.String(required=True, allow_none=False, metadata={"title": _lt("Redirect URL"), "description": _lt("Redirect URL when user picks suitable payment method"), "example": "https://example.com/method/result"})
    webhook = fields.String(required=False, allow_none=False, metadata={"title": _lt("Webhook URL"), "description": _lt("Webhook URL to send a notification"), "example": "https://example.com/method/webhook"})


class PaymentPrepareMethod(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.method"

    virtualPos = NestedModel("payment.prepare.method.item", required=False, metadata={"title": _lt("Virtual PoS payment"), "description": _lt("Attributes when card payment is selected")})
    physicalPos = NestedModel("payment.prepare.method.physicalPos", required=False, metadata={"title": _lt("Physical PoS"), "description": _lt("Attributes when physical PoS is selected")})
    shoppingCredit = NestedModel("payment.prepare.method.item", required=False, metadata={"title": _lt("Shopping credit"), "description": _lt("Attributes when shopping credit is selected")})
    bankTransfer = NestedModel("payment.prepare.method.item", required=False, metadata={"title": _lt("Bank transfer"), "description": _lt("Attributes when bank payment is selected")})


class PaymentInstallmentOption(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.installment.option"

    count = fields.Integer(metadata={"title": _lt("Installment Count"), "description": _lt("Installment count"), "example": 1})
    amount = fields.Float(metadata={"title": _lt("Installment Amount"), "description": _lt("Installment amount"), "example": 123.45})
    rate_cost = fields.Float(metadata={"title": _lt("Cost Rate"), "description": _lt("Cost rate"), "example": 1})
    rate_customer = fields.Float(metadata={"title": _lt("Customer Rate"), "description": _lt("Customer rate"), "example": 2})
    plus_count = fields.Integer(metadata={"title": _lt("Plus Installment Count"), "description": _lt("Plus installment count"), "example": 3})
    plus_desc = fields.String(metadata={"title": _lt("Plus Installment Description"), "description": _lt("Plus installment description"), "example": "+3 Installment"})
    min_amount = fields.Float(metadata={"title": _lt("Minimum Amount"), "description": _lt("Minimum amount limit for this option to be used"), "example": 100.0})
    max_amount = fields.Float(metadata={"title": _lt("Maximum Amount"), "description": _lt("Maximum amount limit for this option to be used"), "example": 0.0})
    min_rate_customer = fields.Float(metadata={"title": _lt("Minimum Customer Rate"), "description": _lt("Minimum customer rate for this installment option"), "example": 1.0})
    max_rate_customer = fields.Float(metadata={"title": _lt("Maximum Customer Rate"), "description": _lt("Maximum customer rate for this installment option"), "example": 0.0})


class PaymentInstallmentList(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.installment.list"

    family = fields.String(metadata={"title": _lt("Card Family"), "description": _lt("Card family name"), "example": "Bankkart"})
    logo = fields.String(metadata={"title": _lt("Card Logo"), "description": _lt("Card family logo address"), "example": "https://paylox/card/logo"})
    type = fields.String(allow_none=True, metadata={"title": _lt("Card Type"), "description": _lt("Card type information"), "example": "Credit"})
    currency = fields.String(metadata={"title": _lt("Currency Code"), "description": _lt("ISO Code of currency"), "example": "TRY"})
    campaign = fields.String(metadata={"title": _lt("Campaign Name"), "description": _lt("Name of campaign"), "example": "Standard"})
    period = fields.Integer(metadata={"title": _lt("Installment Period"), "description": _lt("Installment period"), "example": 1})
    excluded = fields.List(fields.String(), allow_none=True, metadata={"title": _lt("Excluded BINs"), "description": _lt("Excluded BIN numbers which are not going to benefit from related installment options"), "example": "456789"})
    options = fields.List(NestedModel("payment.installment.option"), metadata={"title": _lt("Installment Options"), "description": _lt("All installment options related to given installment information")})


class PaymentInstallmentInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.installment.input"
    _inherit = "payment.credential.apikey"

    amount = fields.Float(metadata={"title": _lt("Amount"), "description": _lt("Amount to pay"), "example": 145.3, "default": 0.0})
    currency = fields.String(metadata={"title": _lt("Currency Code"), "description": _lt("ISO Code of currency to be used in getting installment options"), "example": "TRY", "default": "TRY"})
    campaign = fields.String(metadata={"title": _lt("Campaign Name"), "description": _lt("Name of campaign to be used in getting installment options"), "example": "Standard", "default": ""})
    type = fields.String(metadata={"title": _lt("Card Type"), "description": _lt("Information whether card is debit or credit or something else"), "example": "AllTypes", "default": "AllTypes"})
    bin = fields.String(allow_none=False, metadata={"title": _lt("BIN Number"), "description": _lt("First six digits of card number (Do not use this parameter if you want to get all installment options)"), "example": "456789"})

class PaymentInstallmentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.installment.output"
    _inherit = "payment.output"

    installments = fields.List(NestedModel("payment.installment.list"), metadata={"title": _lt("Installment List"), "description": _lt("List of all installments related to request")})


class PaymentPrepareInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.input"
    _inherit = "payment.credential.hash"

    id = fields.String(required=True, allow_none=False, metadata={"title": "ID", "description": _lt("Any unique identifier related to your specified record in your database for tracking the payment flow"), "example": '12aaff56a'})
    expiration = fields.DateTime(allow_none=False, metadata={"title": _lt("Expiration Date"), "description": _lt("Datetime in ISO format to get transaction expired"), "example": "2023-01-01T00:00:00"})
    campaign = fields.String(metadata={"title": _lt("Campaign Name"), "description": _lt("Name of campaign to be used in getting installment options"), "example": "Standard"})
    partner = NestedModel("payment.partner", required=True, metadata={"title": _lt("Partner information related to request"), "description": _lt("Partner information")})
    order = NestedModel("payment.order", required=True, metadata={"title": _lt("Order information related to request"), "description": _lt("Order details")})
    html = fields.String(metadata={"title": _lt("Custom HTML"), "description": _lt("Custom code to be viewed bottom of the page"), "example": "<p>Copyright</p>"})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Amount"), "description": _lt("Amount to pay"), "example": 145.3})
    installmentCount = fields.Integer(required=False, allow_none=False, validate=validate.NoneOf([0]), metadata={"title": _lt("Installment Count"), "description": _lt("Installment count"), "example": 1, "default": 1})
    methods = NestedModel("payment.prepare.method", required=True, allow_none=False, metadata={"title": _lt("Method List"), "description": _lt("List of codes of methods. Possible keys are 'virtualPos', 'physicalPos', 'shoppingCredit', 'bankTransfer'.")})
    payNow = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Begin Payment Process Now"), "description": _lt("Do not redirect to a payment page and process the transaction immediately"), "example": False})


class PaymentPrepareOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.prepare.output"
    _inherit = "payment.output"

    hash = fields.String(required=False, allow_none=False, metadata={"title": _lt("Hash Data"), "description": _lt("Encrypted data to check if hash is created successfully"), "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})
    url = fields.String(required=False, allow_none=False, metadata={"title": _lt("Payment URL"), "description": _lt("Payment URL which redirects to payment page"), "example": "https://example.com/payment?=LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})


class PaymentInstallment(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.installment"

    amount = fields.Float(metadata={"title": _lt("Installment Amount"), "description": _lt("Monthly payment amount"), "example": 18.16})
    count = fields.Integer(metadata={"title": _lt("Installment Count"), "description": _lt("Total applied installment count if exist"), "example": 8})
    description = fields.String(metadata={"title": _lt("Installment Description"), "description": _lt("Statement describing how installement count is formed"), "example": "6+2 (+2 Campaign)"})


class PaymentInitCard(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.init.card"

    name = fields.String(required=True, metadata={"title": _lt("Credit Card Holder Name"), "description": _lt("Name field which is placed on front side of the card"), "example": "John Doe"})
    number = fields.String(required=True, metadata={"title": _lt("Credit Card Number"), "description": _lt("Masked number of related credit card"), "example": "123478******1234"})
    expiry_month = fields.String(required=True, metadata={"title": _lt("Credit Card Expiry Month"), "description": _lt("Month of expiry date of credit card"), "example": "12"})
    expiry_year = fields.String(required=True, metadata={"title": _lt("Credit Card Expiry Year"), "description": _lt("Year of expiry date of credit card"), "example": "30"})
    cvc = fields.String(required=True, metadata={"title": _lt("Credit Card Security Code"), "description": _lt("CVC code of credit card"), "example": "000"})


class PaymentInitInput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.init.input"
    _inherit = "payment.credential.hash"

    #hash = fields.String(required=True, allow_none=False, metadata={"title": _lt("Hash Data"), "description": _lt("Calculated as the following: 'BASE64_ENCODE(SHA_256(APPLICATION_KEY + CARD_NUMBER + AMOUNT + SECRET_KEY))'."), "example": "LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})
    card = NestedModel("payment.init.card", required=True, metadata={"title": _lt("Credit card information related to transaction"), "description": _lt("Credit card details")})
    partner = NestedModel("payment.partner", required=True, metadata={"title": _lt("Partner information related to request"), "description": _lt("Partner information")})
    campaign = fields.String(metadata={"title": _lt("Campaign Name"), "description": _lt("Name of campaign to be used in getting installment options"), "example": "Standard"})
    id = fields.String(required=True, allow_none=False, metadata={"title": "ID", "description": _lt("Any unique identifier related to your specified record in your database for tracking the payment flow"), "example": '12aaff56a'})
    currency = fields.String(required=False, allow_none=False, metadata={"title": _lt("Currency"), "description": _lt("Payment currency"), "example": "TRY"})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Amount"), "description": _lt("Amount to pay"), "example": 145.3})
    installmentCount = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Installment Count"), "description": _lt("Installment count"), "example": 4})
    successUrl = fields.String(required=True, allow_none=False, metadata={"title": _lt("Success URL"), "description": _lt("If process result is success, it will be posted this url with order id"), "example": "https://api.payment.com/api/v1/success"})
    failUrl = fields.String(required=True, allow_none=False, metadata={"title": _lt("Fail URL"), "description": _lt("If process result is failed, it will be posted this url with order id"), "example": "https://api.payment.com/api/v1/fail"})


class PaymentInitOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "payment.init.output"
    _inherit = "payment.output"

    suggestion = fields.String(required=False, allow_none=False, metadata={"title": _lt("Suggestion"), "description": _lt("This is the suggestion about you can take the action if the payment fails"), "example": "Suggestion about payment success"})
    service_resp_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("Service Response Code"), "description": _lt("Payment service response code"), "example": "5062"})
    service_resp_message = fields.String(required=False, allow_none=False, metadata={"title": _lt("Service Response Message"), "description": _lt("Payment service response message"), "example": "Gönderilen tutar tüm kırılımların toplam tutarına eşit olmalıdır"})
    transaction_id = fields.String(required=False, allow_none=False, metadata={"title": _lt("Transaction ID"), "description": _lt("This is the unique id of your payment request in our system. You need to post it to redirect url when redirection needed"), "example": "a9bcbe48-0543-4a0d-be41-e423b64a5550"})
    url_redirect = fields.String(required=False, allow_none=False, metadata={"title": _lt("Redirect URL"), "description": _lt("If the status code is 307 you need to redirect this url with transaction_id (that we returned in this response) on the form data"), "example": "https://api.payment.com/api/v1/"})
    virtual_pos_name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual Pos Name"), "description": _lt("Virtual pos name the payment processed"), "example": "Garanti Sanal Pos"})
    virtual_pos_id = fields.Integer(required=False, allow_none=False, metadata={"title": _lt("Virtual Pos ID"), "description": _lt("Virtual pos id the payment processed"), "example": 35})
    auth_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("Auth Code"), "description": _lt("Bank authorization code"), "example": "058942"})
    bin_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual Pos Name"), "description": _lt("Virtual pos name the payment processed"), "example": "521807"})
    installment_count = fields.Integer(required=False, allow_none=False, metadata={"title": _lt("Installment Count"), "description": _lt("Installment Count"), "example": 4})
    currency = fields.String(required=False, allow_none=False, metadata={"title": _lt("Currency"), "description": _lt("Payment currency"), "example": "TRY"})
    amount = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Amount"), "description": _lt("Payment amount"), "example": 150.25})
    cost_rate = fields.Float(metadata={"title": _lt("Cost Commision Rate"), "description": _lt("Percentage which is subtracted from total payment amount"), "example": 1.5})
    cost_amount = fields.Float(metadata={"title": _lt("Cost Commision Amount"), "description": _lt("Amount which is subtracted from total payment amount"), "example": 2.18})
    card_type = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual Pos Name"), "description": _lt("Virtual pos name the payment processed"), "example": "Credit"})
    card_program = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual Pos Name"), "description": _lt("Virtual pos name the payment processed"), "example": "Mastercard"})
    card_family = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual Pos Name"), "description": _lt("Virtual pos name the payment processed"), "example": "Axess"})
    card_bank_eft_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual Pos Name"), "description": _lt("Virtual pos name the payment processed"), "example": "046"})
    card_bank_name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Card Bank Name"), "description": _lt("Card Bank Name"), "example": "Akbank T.A.Ş."})


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
    transaction_id = fields.String(metadata={"title": _lt("Payment TransactionID"), "description": _lt("Special value which is generated especially for payments"), "example": "v3a2a10684j94ue0151z7f2e9bbdvd0p"})
    message = fields.String(metadata={"title": _lt("State Message"), "description": _lt("Description of payment transaction"), "example": "Transaction is successful"})
    service_code = fields.String(metadata={"title": _lt("Service Code"), "description": _lt("Service Code"), "example": "Transaction is successful"})
    service_message = fields.String(metadata={"title": _lt("Service Message"), "description": _lt("Service Message"), "example": "Transaction is successful"})
    service_suggestion = fields.String(metadata={"title": _lt("Service Suggestion"), "description": _lt("Service Suggestion"), "example": "Transaction is successful"})
    partner = NestedModel("payment.transaction.partner", metadata={"title": _lt("Partner related to transaction"), "description": _lt("Partner details")})
    card = NestedModel("payment.card", metadata={"title": _lt("Credit card information related to transaction"), "description": _lt("Credit card details")})
    credit = NestedModel("payment.credit", metadata={"title": _lt("Shopping credit information related to transaction"), "description": _lt("Shopping credit details")})
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
    auth_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("Authorization Code"), "description": _lt("Authorization Code"), "example": ""})
    card_type = fields.String(required=False, allow_none=False, metadata={"title": _lt("Credit Card Type"), "description": _lt("Credit Card Type"), "example": ""})
    card_program = fields.String(required=False, allow_none=False, metadata={"title": _lt("Credit Card Program"), "description": _lt("Credit Card Program"), "example": ""})
    card_family = fields.String(required=False, allow_none=False, metadata={"title": _lt("Credit Card Family"), "description": _lt("Credit Card Family"), "example": ""})
    bin_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("BIN Code"), "description": _lt("BIN Code"), "example": ""})
    vpos_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual PoS Code"), "description": _lt("Virtual PoS Code"), "example": ""})
    vpos_name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual PoS Name"), "description": _lt("Virtual PoS Name"), "example": ""})
    vpos_ref = fields.String(required=False, allow_none=False, metadata={"title": _lt("Virtual PoS Reference"), "description": _lt("Virtual PoS Reference"), "example": ""})
    vpos_id = fields.Integer(required=False, allow_none=False, metadata={"title": _lt("Virtual PoS ID"), "description": _lt("Virtual PoS ID"), "example": 0})
    service_code = fields.String(required=False, allow_none=False, metadata={"title": _lt("Service Code"), "description": _lt("Service Code"), "example": ""})
    service_message = fields.String(required=False, allow_none=False, metadata={"title": _lt("Service Message"), "description": _lt("Service Message"), "example": ""})
    service_ref_id = fields.String(required=False, allow_none=False, metadata={"title": _lt("Service ReferenceID"), "description": _lt("Service ReferenceID"), "example": ""})
    preauth = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Pre-Authorization"), "description": _lt("Pre-Authorization"), "example": False})
    postauth = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Post-Authorization"), "description": _lt("Post-Authorization"), "example": False})
