# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo import _lt
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class EscrowResponse(Datamodel):
    class Meta:
        ordered = True

    _name = "escrow.response"

    status = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Response Code"), "description": _lt("Integer which is returned to represent response"), "example": 0})
    message = fields.String(required=True, allow_none=False, metadata={"title": _lt("Response Message"), "description": _lt("Description which is returned to represent response"), "example": "Success"})


class EscrowRequestAdOwnerBanks(Datamodel):
    _inherit = "payment.partner.bank"
    _name = "escrow.request.ad.owner.banks"

    merchant = fields.String(required=True, allow_none=False, metadata={"title": _lt("Merchant Name"), "description": _lt("Merchant name"), "example": "Jane Doe Inc."})


class EscrowRequestAdOwner(Datamodel):
    _name = "escrow.request.ad.owner"

    class Meta:
        ordered = True

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Partner Name"), "description": _lt("Partner name"), "example": "John Doe"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": _lt("Partner VAT"), "description": _lt("Partner VAT number"), "example": "12345678910"})
    taxOffice = fields.String(required=False, allow_none=False, metadata={"title": _lt("Partner Tax Office"), "description": _lt("Partner tax office (required if lenght of VAT is ten)"), "example": "MERKEZ"})
    email = fields.String(required=True, allow_none=False, metadata={"title": _lt("Email Address"), "description": _lt("Email address"), "example": "test@example.com"})
    phone = fields.String(required=True, allow_none=False, metadata={"title": _lt("Phone Number"), "description": _lt("Phone number"), "example": "+905321234567"})
    country = fields.String(required=False, allow_none=False, metadata={"title": _lt("Country Code"), "description": _lt("Country code"), "example": "TR"})
    state = fields.String(required=False, allow_none=False, metadata={"title": _lt("State Code"), "description": _lt("State code"), "example": "34"})
    city = fields.String(required=False, allow_none=False, metadata={"title": _lt("City/Town Name"), "description": _lt("City/Town name"), "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=False, metadata={"title": _lt("Partner Address"), "description": _lt("Partner address"), "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=False, metadata={"title": _lt("ZIP Code"), "description": _lt("ZIP Code"), "example": "34100"})
    banks = fields.List(NestedModel("escrow.request.ad.owner.banks"), required=True, allow_none=False, metadata={"title": _lt("List of Bank Accounts"), "description": _lt("List of bank accounts of owner")})


class EscrowRequestBrokerBanks(Datamodel):
    _inherit = "payment.partner.bank"
    _name = "escrow.request.broker.banks"

    merchant = fields.String(required=True, allow_none=False, metadata={"title": _lt("Merchant Name"), "description": _lt("Merchant name"), "example": "Jane Doe Inc."})


class EscrowRequestBroker(Datamodel):
    _name = "escrow.request.broker"

    class Meta:
        ordered = True

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Broker Name"), "description": _lt("Broker name"), "example": "John Doe Broker"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": _lt("Broker VAT"), "description": _lt("Broker VAT number"), "example": "12345678910"})
    taxOffice = fields.String(required=False, allow_none=False, metadata={"title": _lt("Broker Tax Office"), "description": _lt("Broker tax office (required if lenght of VAT is ten)"), "example": "MERKEZ"})
    email = fields.String(required=True, allow_none=False, metadata={"title": _lt("Email Address"), "description": _lt("Email address"), "example": "broker@example.com"})
    phone = fields.String(required=True, allow_none=False, metadata={"title": _lt("Phone Number"), "description": _lt("Phone number"), "example": "+905321234567"})
    country = fields.String(required=False, allow_none=False, metadata={"title": _lt("Country Code"), "description": _lt("Country code"), "example": "TR"})
    state = fields.String(required=False, allow_none=False, metadata={"title": _lt("State Code"), "description": _lt("State code"), "example": "34"})
    city = fields.String(required=False, allow_none=False, metadata={"title": _lt("City/Town Name"), "description": _lt("City/Town name"), "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=False, metadata={"title": _lt("Broker Address"), "description": _lt("Broker address"), "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=False, metadata={"title": _lt("ZIP Code"), "description": _lt("ZIP Code"), "example": "34100"})
    banks = fields.List(NestedModel("escrow.request.broker.banks"), required=True, allow_none=False, metadata={"title": _lt("List of Bank Accounts"), "description": _lt("List of bank accounts of broker")})


class EscrowRequestAd(Datamodel):
    _name = "escrow.request.ad"

    class Meta:
        ordered = True

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Name"), "description": _lt("Ad name"), "example": "Advertisement"})
    reference = fields.String(required=True, allow_none=False, metadata={"title": _lt("Reference"), "description": _lt("Ad reference"), "example": "AD001"})
    description = fields.String(required=True, allow_none=False, metadata={"title": _lt("Description"), "description": _lt("Ad description in HTML format"), "example": "<h1>Description</h1>"})
    owner = NestedModel("escrow.request.ad.owner", required=True, allow_none=False, metadata={"title": _lt("Owner information"), "description": _lt("Owner information related to request")})
    price = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Price Unit"), "description": _lt("Price unit"), "example": 145.3})
    images = fields.List(fields.String, required=False, allow_none=False, metadata={"title": _lt("Images"), "description": _lt("Array of ad images which are encoded with base64"), "example": []})


class EscrowRequestAdsCreate(Datamodel):
    _name = "escrow.request.ads.create"

    class Meta:
        ordered = True

    ads = fields.List(NestedModel("escrow.request.ad"), required=True, allow_none=False, metadata={"title": _lt("Array of Ads"), "description": _lt("Array of ads")})


class EscrowResponseAdsCreateAds(Datamodel):
    _name = "escrow.response.ads.create.ads"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Ad unique number"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    reference = fields.String(required=True, allow_none=False, metadata={"title": _lt("Reference"), "description": _lt("Ad reference"), "example": "AD001"})


class EscrowResponseAdsCreate(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.ads.create"

    class Meta:
        ordered = True

    ads = fields.List(NestedModel("escrow.response.ads.create.ads"), required=True, allow_none=False, metadata={"title": _lt("Ads"), "description": _lt("Array of ads")})


class EscrowRequestAdsReadPage(Datamodel):
    _name = "escrow.request.ads.read.page"

    class Meta:
        ordered = True

    size = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Size"), "description": _lt("Page size"), "example": 10})
    number = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Number"), "description": _lt("Page number"), "example": 1})


class EscrowRequestAdsRead(Datamodel):
    _name = "escrow.request.ads.read"

    class Meta:
        ordered = True

    page = NestedModel("escrow.request.ads.read.page", required=True, allow_none=False, metadata={"title": _lt("Page"), "description": _lt("Page options")})
    ads = fields.List(fields.UUID, required=False, allow_none=True, metadata={"title": _lt("Ads"), "description": _lt("Array of ads"), "example": ["9ee3fd53-42f9-4f16-b454-77e6b714c2e9"]})


class EscrowResponseAdsReadPage(Datamodel):
    _name = "escrow.response.ads.read.page"

    class Meta:
        ordered = True

    size = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Size"), "description": _lt("Requested page size"), "example": 10})
    number = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Number"), "description": _lt("Current page number"), "example": 1})
    count = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Count"), "description": _lt("Total page count"), "example": 1})


class EscrowResponseAdsReadAds(Datamodel):
    _name = "escrow.response.ads.read.ads"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Ad unique number"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Name"), "description": _lt("Ad name"), "example": "Advertisement"})
    reference = fields.String(required=True, allow_none=False, metadata={"title": _lt("Reference"), "description": _lt("Ad reference"), "example": "AD001"})
    description = fields.String(required=True, allow_none=False, metadata={"title": _lt("Description"), "description": _lt("Ad description in HTML format"), "example": "<h1>Description</h1>"})
    owner = NestedModel("escrow.request.ad.owner", required=True, allow_none=False, metadata={"title": _lt("Owner information"), "description": _lt("Owner information related to request")})
    price = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Price Unit"), "description": _lt("Price unit"), "example": 145.3})
    images = fields.List(fields.String, required=False, allow_none=False, metadata={"title": _lt("Images"), "description": _lt("Array of ad images which are encoded with base64"), "example": []})


class EscrowResponseAdsRead(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.ads.read"

    class Meta:
        ordered = True


    page = NestedModel("escrow.response.ads.read.page", required=True, allow_none=False, metadata={"title": _lt("Page"), "description": _lt("Page information")})
    ads = fields.List(NestedModel("escrow.response.ads.read.ads"), required=True, allow_none=False, metadata={"title": _lt("Ads"), "description": _lt("Array of ads")})


class EscrowRequestAdsUpdateAdsOwnerBanks(Datamodel):
    _name = "escrow.request.ads.update.ads.owner.banks"

    name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Account Name"), "description": _lt("Account name"), "example": "Bank Account"})
    iban = fields.String(required=True, allow_none=False, metadata={"title": _lt("Account IBAN"), "description": _lt("Account IBAN"), "example": "TR000000000000000000000000"})
    merchant = fields.String(required=False, allow_none=False, metadata={"title": _lt("Merchant Name"), "description": _lt("Merchant name"), "example": "Jane Doe Inc."})


class EscrowRequestAdsUpdateAdsOwner(Datamodel):
    _name = "escrow.request.ads.update.ads.owner"

    class Meta:
        ordered = True

    name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Partner Name"), "description": _lt("Partner name"), "example": "John Doe"})
    vat = fields.String(required=False, allow_none=False, metadata={"title": _lt("Partner VAT"), "description": _lt("Partner VAT number"), "example": "12345678910"})
    taxOffice = fields.String(required=False, allow_none=False, metadata={"title": _lt("Partner Tax Office"), "description": _lt("Partner tax office (required if lenght of VAT is ten)"), "example": "MERKEZ"})
    email = fields.String(required=False, allow_none=False, metadata={"title": _lt("Email Address"), "description": _lt("Email address"), "example": "test@example.com"})
    phone = fields.String(required=False, allow_none=False, metadata={"title": _lt("Phone Number"), "description": _lt("Phone number"), "example": "+905321234567"})
    country = fields.String(required=False, allow_none=True, metadata={"title": _lt("Country Code"), "description": _lt("Country code"), "example": "TR"})
    state = fields.String(required=False, allow_none=True, metadata={"title": _lt("State Code"), "description": _lt("State code"), "example": "34"})
    city = fields.String(required=False, allow_none=True, metadata={"title": _lt("City/Town Name"), "description": _lt("City/Town name"), "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=True, metadata={"title": _lt("Partner Address"), "description": _lt("Partner address"), "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=True, metadata={"title": _lt("ZIP Code"), "description": _lt("ZIP Code"), "example": "34100"})
    banks = fields.List(NestedModel("escrow.request.ads.update.ads.owner.banks"), required=False, allow_none=False, metadata={"title": _lt("List of Bank Accounts"), "description": _lt("List of bank accounts of owner")})


class EscrowRequestAdsUpdateAds(Datamodel):
    _name = "escrow.request.ads.update.ads"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Ad unique number"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Name"), "description": _lt("Ad name"), "example": "Advertisement"})
    reference = fields.String(required=False, allow_none=False, metadata={"title": _lt("Reference"), "description": _lt("Ad reference"), "example": "AD001"})
    description = fields.String(required=False, allow_none=False, metadata={"title": _lt("Description"), "description": _lt("Ad description in HTML format"), "example": "<h1>Description</h1>"})
    owner = NestedModel("escrow.request.ads.update.ads.owner", required=False, allow_none=False, metadata={"title": _lt("Owner information"), "description": _lt("Owner information related to request")})
    price = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Price Unit"), "description": _lt("Price unit"), "example": 145.3})
    images = fields.List(fields.String, required=False, allow_none=True, metadata={"title": _lt("Images"), "description": _lt("Array of ad images which are encoded with base64"), "example": []})


class EscrowRequestAdsUpdate(Datamodel):
    _name = "escrow.request.ads.update"

    class Meta:
        ordered = True

    ads = fields.List(NestedModel("escrow.request.ads.update.ads"), required=True, allow_none=False, metadata={"title": _lt("Array of Ads"), "description": _lt("Array of ads")})


class EscrowResponseAdsUpdate(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.ads.update"

    class Meta:
        ordered = True

    ads = fields.List(NestedModel("escrow.response.ads.create.ads"), required=True, allow_none=False, metadata={"title": _lt("Ads"), "description": _lt("Array of ads")})


class EscrowRequestAdsDelete(Datamodel):
    _name = "escrow.request.ads.delete"

    class Meta:
        ordered = True

    ads = fields.List(fields.UUID, required=True, allow_none=False, metadata={"title": _lt("Ads"), "description": _lt("Array of ads"), "example": ["9ee3fd53-42f9-4f16-b454-77e6b714c2e9"]})


class EscrowResponseAdsDelete(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.ads.delete"

    class Meta:
        ordered = True

    ads = fields.List(NestedModel("escrow.response.ads.create.ads"), required=True, allow_none=False, metadata={"title": _lt("Ads"), "description": _lt("Array of ads")})


# Broker Datamodels


class EscrowRequestBrokersCreate(Datamodel):
    _name = "escrow.request.brokers.create"

    class Meta:
        ordered = True

    brokers = fields.List(NestedModel("escrow.request.broker"), required=True, allow_none=False, metadata={"title": _lt("Array of Brokers"), "description": _lt("Array of brokers")})


class EscrowResponseBrokersCreateBrokers(Datamodel):
    _name = "escrow.response.brokers.create.brokers"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Broker unique number"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": _lt("VAT"), "description": _lt("Broker VAT number"), "example": "12345678910"})


class EscrowResponseBrokersCreate(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.brokers.create"

    class Meta:
        ordered = True

    brokers = fields.List(NestedModel("escrow.response.brokers.create.brokers"), required=True, allow_none=False, metadata={"title": _lt("Brokers"), "description": _lt("Array of brokers")})


class EscrowRequestBrokersReadPage(Datamodel):
    _name = "escrow.request.brokers.read.page"

    class Meta:
        ordered = True

    size = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Size"), "description": _lt("Page size"), "example": 10})
    number = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Number"), "description": _lt("Page number"), "example": 1})


class EscrowRequestBrokersRead(Datamodel):
    _name = "escrow.request.brokers.read"

    class Meta:
        ordered = True

    page = NestedModel("escrow.request.brokers.read.page", required=True, allow_none=False, metadata={"title": _lt("Page"), "description": _lt("Page options")})
    brokers = fields.List(fields.UUID, required=False, allow_none=True, metadata={"title": _lt("Brokers"), "description": _lt("Array of brokers"), "example": ["9ee3fd53-42f9-4f16-b454-77e6b714c2e9"]})


class EscrowResponseBrokersReadPage(Datamodel):
    _name = "escrow.response.brokers.read.page"

    class Meta:
        ordered = True

    size = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Size"), "description": _lt("Requested page size"), "example": 10})
    number = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Number"), "description": _lt("Current page number"), "example": 1})
    count = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Page Count"), "description": _lt("Total page count"), "example": 1})


class EscrowResponseBrokersReadBrokers(Datamodel):
    _name = "escrow.response.brokers.read.brokers"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Broker unique number"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Name"), "description": _lt("Broker name"), "example": "John Doe Broker"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": _lt("VAT"), "description": _lt("Broker VAT number"), "example": "12345678910"})
    taxOffice = fields.String(required=False, allow_none=False, metadata={"title": _lt("Tax Office"), "description": _lt("Broker tax office"), "example": "MERKEZ"})
    email = fields.String(required=True, allow_none=False, metadata={"title": _lt("Email Address"), "description": _lt("Email address"), "example": "broker@example.com"})
    phone = fields.String(required=True, allow_none=False, metadata={"title": _lt("Phone Number"), "description": _lt("Phone number"), "example": "+905321234567"})
    country = fields.String(required=False, allow_none=False, metadata={"title": _lt("Country Code"), "description": _lt("Country code"), "example": "TR"})
    state = fields.String(required=False, allow_none=False, metadata={"title": _lt("State Code"), "description": _lt("State code"), "example": "34"})
    city = fields.String(required=False, allow_none=False, metadata={"title": _lt("City/Town Name"), "description": _lt("City/Town name"), "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=False, metadata={"title": _lt("Broker Address"), "description": _lt("Broker address"), "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=False, metadata={"title": _lt("ZIP Code"), "description": _lt("ZIP Code"), "example": "34100"})
    banks = fields.List(NestedModel("escrow.request.broker.banks"), required=True, allow_none=False, metadata={"title": _lt("List of Bank Accounts"), "description": _lt("List of bank accounts of broker")})


class EscrowResponseBrokersRead(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.brokers.read"

    class Meta:
        ordered = True

    page = NestedModel("escrow.response.brokers.read.page", required=True, allow_none=False, metadata={"title": _lt("Page"), "description": _lt("Page information")})
    brokers = fields.List(NestedModel("escrow.response.brokers.read.brokers"), required=True, allow_none=False, metadata={"title": _lt("Brokers"), "description": _lt("Array of brokers")})


class EscrowRequestBrokersUpdateBrokersBanks(Datamodel):
    _name = "escrow.request.brokers.update.brokers.banks"

    name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Account Name"), "description": _lt("Account name"), "example": "Bank Account"})
    iban = fields.String(required=True, allow_none=False, metadata={"title": _lt("Account IBAN"), "description": _lt("Account IBAN"), "example": "TR000000000000000000000000"})
    merchant = fields.String(required=False, allow_none=False, metadata={"title": _lt("Merchant Name"), "description": _lt("Merchant name"), "example": "Jane Doe Inc."})


class EscrowRequestBrokersUpdateBrokers(Datamodel):
    _name = "escrow.request.brokers.update.brokers"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Broker unique number"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    name = fields.String(required=False, allow_none=False, metadata={"title": _lt("Broker Name"), "description": _lt("Broker name"), "example": "John Doe Broker"})
    vat = fields.String(required=False, allow_none=False, metadata={"title": _lt("Broker VAT"), "description": _lt("Broker VAT number"), "example": "12345678910"})
    taxOffice = fields.String(required=False, allow_none=False, metadata={"title": _lt("Broker Tax Office"), "description": _lt("Broker tax office"), "example": "MERKEZ"})
    email = fields.String(required=False, allow_none=False, metadata={"title": _lt("Email Address"), "description": _lt("Email address"), "example": "broker@example.com"})
    phone = fields.String(required=False, allow_none=False, metadata={"title": _lt("Phone Number"), "description": _lt("Phone number"), "example": "+905321234567"})
    country = fields.String(required=False, allow_none=True, metadata={"title": _lt("Country Code"), "description": _lt("Country code"), "example": "TR"})
    state = fields.String(required=False, allow_none=True, metadata={"title": _lt("State Code"), "description": _lt("State code"), "example": "34"})
    city = fields.String(required=False, allow_none=True, metadata={"title": _lt("City/Town Name"), "description": _lt("City/Town name"), "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=True, metadata={"title": _lt("Broker Address"), "description": _lt("Broker address"), "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=True, metadata={"title": _lt("ZIP Code"), "description": _lt("ZIP Code"), "example": "34100"})
    banks = fields.List(NestedModel("escrow.request.brokers.update.brokers.banks"), required=False, allow_none=False, metadata={"title": _lt("List of Bank Accounts"), "description": _lt("List of bank accounts of broker")})


class EscrowRequestBrokersUpdate(Datamodel):
    _name = "escrow.request.brokers.update"

    class Meta:
        ordered = True

    brokers = fields.List(NestedModel("escrow.request.brokers.update.brokers"), required=True, allow_none=False, metadata={"title": _lt("Array of Brokers"), "description": _lt("Array of brokers")})


class EscrowResponseBrokersUpdate(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.brokers.update"

    class Meta:
        ordered = True

    brokers = fields.List(NestedModel("escrow.response.brokers.create.brokers"), required=True, allow_none=False, metadata={"title": _lt("Brokers"), "description": _lt("Array of brokers")})


class EscrowRequestBrokersDelete(Datamodel):
    _name = "escrow.request.brokers.delete"

    class Meta:
        ordered = True

    brokers = fields.List(fields.UUID, required=True, allow_none=False, metadata={"title": _lt("Brokers"), "description": _lt("Array of brokers"), "example": ["9ee3fd53-42f9-4f16-b454-77e6b714c2e9"]})


class EscrowResponseBrokersDelete(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.brokers.delete"

    class Meta:
        ordered = True

    brokers = fields.List(NestedModel("escrow.response.brokers.create.brokers"), required=True, allow_none=False, metadata={"title": _lt("Brokers"), "description": _lt("Array of brokers")})


class EscrowResponsePaymentTransaction(Datamodel):
    class Meta:
        ordered = True

    _inherit = "payment.transaction"
    _name = "escrow.response.payment.transaction"

    ad = NestedModel("escrow.request.ad", allow_none=False, metadata={"title": _lt("Ad"), "description": _lt("Ad information")})


class EscrowResponsePaymentWebhook(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.payment.webhook"

    class Meta:
        ordered = True

    transaction = NestedModel("escrow.response.payment.transaction", metadata={"title": _lt("Transaction information related to request"), "description": _lt("Transaction details")})


class EscrowRequestPaymentResult(Datamodel):
    _name = "escrow.request.payment.result"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Unique identifier of payment"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})


class EscrowResponsePaymentResult(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.payment.result"

    class Meta:
        ordered = True

    transaction = NestedModel("escrow.response.payment.transaction", metadata={"title": _lt("Transaction information related to request"), "description": _lt("Transaction details")})


class EscrowRequestPaymentPrepareAds(Datamodel):
    _name = "escrow.request.payment.prepare.ads"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": "ID", "description": _lt("Unique identifier of related ad"), "example": '1x2cdaa3-35df-2eff-aeq2-5d74387701xd'})
    price = fields.Float(required=False, allow_none=False, metadata={"title": _lt("Price Unit"), "description": _lt("Price unit"), "example": 145.3})


class EscrowRequestPaymentPrepareCustomer(Datamodel):
    _name = "escrow.request.payment.prepare.customer"

    class Meta:
        ordered = True

    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Customer Name"), "description": _lt("Customer name"), "example": "John Doe"})
    vat = fields.String(required=True, allow_none=False, metadata={"title": _lt("Customer VAT"), "description": _lt("Customer VAT number"), "example": "12345678910"})
    taxOffice = fields.String(required=False, allow_none=False, metadata={"title": _lt("Customer Tax Office"), "description": _lt("Customer tax office (required if lenght of VAT is ten)"), "example": "MERKEZ"})
    email = fields.String(required=True, allow_none=False, metadata={"title": _lt("Email Address"), "description": _lt("Email address"), "example": "test@example.com"})
    phone = fields.String(required=True, allow_none=False, metadata={"title": _lt("Phone Number"), "description": _lt("Phone number"), "example": "+905321234567"})
    country = fields.String(required=True, allow_none=True, metadata={"title": _lt("Country Code"), "description": _lt("Country code"), "example": "TR"})
    state = fields.String(required=True, allow_none=True, metadata={"title": _lt("State Code"), "description": _lt("State code"), "example": "34"})
    city = fields.String(required=False, allow_none=True, metadata={"title": _lt("City/Town Name"), "description": _lt("City/Town name"), "example": "Beyoğlu"})
    address = fields.String(required=False, allow_none=True, metadata={"title": _lt("Customer Address"), "description": _lt("Customer address"), "example": "Example Street, No: 1"})
    zip = fields.String(required=False, allow_none=True, metadata={"title": _lt("ZIP Code"), "description": _lt("ZIP Code"), "example": "34100"})


class EscrowRequestPaymentPrepare(Datamodel):
    _name = "escrow.request.payment.prepare"

    class Meta:
        ordered = True

    reference = fields.String(required=True, allow_none=False, metadata={"title": "Reference", "description": _lt("Any unique identifier related to your specified record in your database for tracking the payment flow"), "example": '12aaff56a'})
    ads = fields.List(NestedModel("escrow.request.payment.prepare.ads"), required=True, allow_none=False, metadata={"title": "Ads", "description": _lt("List of ads")})
    customer = NestedModel("escrow.request.payment.prepare.customer", required=True, allow_none=False, metadata={"title": "Customer", "description": _lt("Customer")})
    redirectUrl = fields.Url(required=True, allow_none=False, metadata={"title": "Redirection URL", "description": _lt("URL to redirect after payment transaction (Transaction identifier will be added to redirection url path, e.g. https://example.com/tx/<id>)"), "example": 'https://example.com/tx'})
    preauth = fields.Boolean(required=False, allow_none=False, metadata={"title": _lt("Pre-Authorization"), "description": _lt("Pre-Authorization"), "example": False})


class EscrowResponsePaymentPrepare(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.payment.prepare"

    class Meta:
        ordered = True

    id = fields.UUID(required=False, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Payment ID"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    url = fields.String(required=False, allow_none=False, metadata={"title": _lt("URL"), "description": _lt("Payment URL which redirects to payment page"), "example": "https://example.com/payment?=LkuxD5WGo/81sqn6ZS6/a0qjdSX1cQWl8tHc5NseGto="})


class EscrowRequestPaymentPostauth(Datamodel):
    _name = "escrow.request.payment.postauth"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Unique identifier of payment"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Postauth Amount"), "description": _lt("Amount to postauth"), "example": 1000.0})


class EscrowResponsePaymentPostauth(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.payment.postauth"

    class Meta:
        ordered = True


class EscrowRequestPaymentCancel(Datamodel):
    _name = "escrow.request.payment.cancel"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Unique identifier of payment"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})


class EscrowResponsePaymentCancel(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.payment.cancel"


class EscrowRequestPaymentRefund(Datamodel):
    _name = "escrow.request.payment.refund"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Unique identifier of payment"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Refund Amount"), "description": _lt("Amount to refund"), "example": 10.71})


class EscrowResponsePaymentRefund(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.payment.refund"


class EscrowRequestPaymentExpire(Datamodel):
    _name = "escrow.request.payment.expire"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Unique identifier of payment"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})


class EscrowResponsePaymentExpire(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.payment.expire"


class EscrowRequestPaymentDelete(Datamodel):
    _name = "escrow.request.payment.delete"

    class Meta:
        ordered = True

    id = fields.UUID(required=True, allow_none=False, metadata={"title": _lt("ID"), "description": _lt("Unique identifier of payment"), "example": "9ee3fd53-42f9-4f16-b454-77e6b714c2e9"})


class EscrowResponsePaymentExpire(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.payment.delete"


class EscrowRequestInsuranceCallback(Datamodel):
    _name = "escrow.request.insurance.callback"

    class Meta:
        ordered = True

    reference = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Quote Reference"), "description": _lt("Insurance quote reference number"), "example": 123456})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Insurance Amount"), "description": _lt("Insurance amount"), "example": 1500.50})
    company = fields.String(required=True, allow_none=False, metadata={"title": _lt("Insurance Company"), "description": _lt("Insurance company name"), "example": "ABC Insurance"})
    commission = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Commission"), "description": _lt("Commission amount"), "example": 150.00})
    policyDoc = fields.String(required=True, allow_none=False, metadata={"title": _lt("Policy Document"), "description": _lt("Policy document file in base64 format"), "example": "JVBERi0xLjQK..."})
    policyNumber = fields.String(required=False, allow_none=True, metadata={"title": _lt("Policy Number"), "description": _lt("Insurance policy number"), "example": "POL-2025-001"})


class EscrowResponseInsuranceCallback(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.insurance.callback"


class EscrowRequestBrokerPaymentLink(Datamodel):
    _name = "escrow.request.broker.payment.link"

    class Meta:
        ordered = True

    broker_id = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Broker ID"), "description": _lt("Broker partner ID"), "example": 123})
    owner_id = fields.Integer(required=False, allow_none=True, metadata={"title": _lt("Owner ID"), "description": _lt("Optional owner partner ID to pre-select on broker link"), "example": 456})


class EscrowResponseBrokerPaymentLink(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.broker.payment.link"

    class Meta:
        ordered = True

    url = fields.String(required=True, allow_none=False, metadata={"title": _lt("Payment Link"), "description": _lt("Broker payment link with token"), "example": "https://example.com/my/ads/broker?token=MTIzOjE3MzY3MzgwMDA="})
    expires_at = fields.DateTime(required=True, allow_none=False, metadata={"title": _lt("Expiry Time"), "description": _lt("Link expiry timestamp"), "example": "2025-01-13 12:00:00"})


class EscrowRequestBrokerRates(Datamodel):
    _name = "escrow.request.broker.rates"

    class Meta:
        ordered = True

    broker_id = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Broker ID"), "description": _lt("Broker partner ID"), "example": 123})
    campaign_id = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Campaign ID"), "description": _lt("Campaign ID to calculate rates"), "example": 1})
    amount = fields.Float(required=False, allow_none=True, metadata={"title": _lt("Amount"), "description": _lt("Transaction amount"), "example": 10000.0})



class EscrowResponseBrokerRatesInstallment(Datamodel):
    _name = "escrow.response.broker.rates.installment"

    class Meta:
        ordered = True

    installment_count = fields.String(required=True, allow_none=False, metadata={"title": _lt("Installment Count"), "description": _lt("Number of installments"), "example": "3"})
    cost_rate = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Cost Rate"), "description": _lt("Bank commission rate percentage"), "example": 2.5})
    broker_rate = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Broker Rate"), "description": _lt("Broker additional commission rate percentage"), "example": 1.5})
    total_rate = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Total Rate"), "description": _lt("Cost rate + Broker rate"), "example": 4.0})
    customer_rate = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Customer Rate"), "description": _lt("Rate reflected to customer"), "example": 4.17})
    total_amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Total Amount"), "description": _lt("Amount to be collected from customer"), "example": 10417.0})


class EscrowResponseBrokerRatesCampaignLine(Datamodel):
    _name = "escrow.response.broker.rates.campaign.line"

    class Meta:
        ordered = True

    card_family = fields.String(required=True, allow_none=False, metadata={"title": _lt("Card Family"), "description": _lt("Card family name"), "example": "Advantage"})
    installments = fields.List(NestedModel("escrow.response.broker.rates.installment"), required=True, allow_none=False, metadata={"title": _lt("Installments"), "description": _lt("Available installment options for this card family")})


class EscrowResponseBrokerRatesRate(Datamodel):
    _name = "escrow.response.broker.rates.rate"

    class Meta:
        ordered = True

    installment_count = fields.String(required=True, allow_none=False, metadata={"title": _lt("Installment Count"), "description": _lt("Number of installments"), "example": "3"})
    broker_additional_rate = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Broker Additional Rate"), "description": _lt("Broker additional commission rate percentage"), "example": 2.5})


class EscrowResponseBrokerRatesCampaign(Datamodel):
    _name = "escrow.response.broker.rates.campaign"

    class Meta:
        ordered = True

    campaign_id = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Campaign ID"), "description": _lt("Campaign ID"), "example": 1})
    campaign_name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Campaign Name"), "description": _lt("Campaign name"), "example": "Summer Campaign"})
    is_default = fields.Boolean(required=True, allow_none=False, metadata={"title": _lt("Is Default"), "description": _lt("Whether this is the default campaign for broker"), "example": True})
    lines = fields.List(NestedModel("escrow.response.broker.rates.campaign.line"), required=True, allow_none=False, metadata={"title": _lt("Lines"), "description": _lt("Installment lines with rates and amounts")})


class EscrowResponseBrokerRates(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.broker.rates"

    class Meta:
        ordered = True

    broker_id = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Broker ID"), "description": _lt("Broker partner ID"), "example": 123})
    broker_name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Broker Name"), "description": _lt("Broker name"), "example": "ABC Broker"})
    campaign_id = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Campaign ID"), "description": _lt("Campaign ID"), "example": 1})
    campaign_name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Campaign Name"), "description": _lt("Campaign name"), "example": "Summer Campaign"})
    amount = fields.Float(required=True, allow_none=False, metadata={"title": _lt("Amount"), "description": _lt("Transaction amount"), "example": 10000.0})
    lines = fields.List(NestedModel("escrow.response.broker.rates.campaign.line"), required=True, allow_none=False, metadata={"title": _lt("Lines"), "description": _lt("Installment lines with rates and amounts")})



class EscrowRequestCampaigns(Datamodel):
    _name = "escrow.request.campaigns"

    class Meta:
        ordered = True


class EscrowResponseCampaignsCampaign(Datamodel):
    _name = "escrow.response.campaigns.campaign"

    class Meta:
        ordered = True

    id = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Campaign ID"), "description": _lt("Campaign unique identifier"), "example": 1})
    name = fields.String(required=True, allow_none=False, metadata={"title": _lt("Campaign Name"), "description": _lt("Campaign name"), "example": "Summer Campaign 2025"})
    sequence = fields.Integer(required=True, allow_none=False, metadata={"title": _lt("Sequence"), "description": _lt("Display sequence"), "example": 10})
    active = fields.Boolean(required=True, allow_none=False, metadata={"title": _lt("Active"), "description": _lt("Whether campaign is active"), "example": True})


class EscrowResponseCampaigns(Datamodel):
    _inherit = "escrow.response"
    _name = "escrow.response.campaigns"

    class Meta:
        ordered = True

    campaigns = fields.List(NestedModel("escrow.response.campaigns.campaign"), required=True, allow_none=False, metadata={"title": _lt("Campaigns"), "description": _lt("List of all active campaigns")})

