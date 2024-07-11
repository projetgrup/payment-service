# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class OrderCheckoutPaymentItemParent(Datamodel):
    _name = "oco.payment.item.parent"

    name = fields.String(required=True, allow_none=False, metadata={"title": "Vendor Name", "description": "Vendor company name", "example": "Jane Doe Inc."})
    vat = fields.String(required=True, allow_none=False, metadata={"title": "Vendor VAT", "description": "VAT number of related oco. The value of this field must be identical to its corresponding record in payment system. Otherwise, new oco will be created with given parameters.", "example": "12345678912"})
    email = fields.String(required=True, allow_none=False, metadata={"title": "Vendor Email", "description": "Email address of related oco", "example": "test@example.com"})
    mobile = fields.String(required=True, allow_none=False, metadata={"title": "Vendor Mobile", "description": "Mobile phone number of related oco", "example": "+905001234567"})
    reference = fields.String(required=False, allow_none=False, metadata={"title": "Vendor Reference Number", "description": "Vendor Reference", "example": "ABC01"})
    campaign = fields.String(required=False, allow_none=False, metadata={"title": "Vendor Campaign Name", "description": "Vendor Campaign", "example": "Standard"})


class OrderCheckoutPaymentItemLine(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.item.line"

    amount = fields.Float(required=True, allow_none=False, metadata={"title": "Amount", "description": "Amount to pay", "example": 1200.0})
    description = fields.String(required=False, allow_none=False, metadata={"title": "Payment Description", "description": "Description about related payment item", "example": "ABC01"})


class OrderCheckoutPaymentItem(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.item"

    vendor = NestedModel("oco.payment.item.parent", required=True, metadata={"title": "Vendor Information", "description": "Vendor information of payment item"})
    payments = fields.List(NestedModel("oco.payment.item.line"), required=True, metadata={"title": "Payment Information", "description": "Payment item details which contains amounts and other informations"})


class OrderCheckoutPaymentTransaction(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.transaction"

    date = fields.String(required=True, allow_none=False, metadata={"title": "Payment Date", "description": "Create date of payment transaction", "example": "26-02-2024 13:17:51"})
    reference = fields.String(required=True, allow_none=False, metadata={"title": "Payment Reference", "description": "Reference code of payment transaction", "example": "fa153e09-43ba-4f52-919b-07bab2cb5725"})
    status = fields.String(required=True, allow_none=False, metadata={"title": "Payment Status", "description": "Status of payment", "example": ""})
    description = fields.String(required=True, allow_none=False, metadata={"title": "Payment Description", "description": "Descriptive message about payment", "example": "done"})
    payment_payable = fields.Float(required=True, allow_none=False, metadata={"title": "Payable Amount", "description": "Initial amount to be paid", "example": 26220})
    customer_rate = fields.Float(required=True, allow_none=False, metadata={"title": "Customer Commission Rate", "description": "Customer commission rate applied to customer", "example": 1.71})
    customer_amount = fields.Float(required=True, allow_none=False, metadata={"title": "Customer Commission Amount", "description": "Customer commission amount applied to customer", "example": 450.74})
    payment_paid = fields.Float(required=True, allow_none=False, metadata={"title": "Paid Amount", "description": "Amount which is paid", "example": 26670.74})
    commission_rate = fields.Float(required=True, allow_none=False, metadata={"title": "Cost Commission Rate", "description": "Cost commission rate applied from provider", "example": 1.69})
    commission_amount = fields.Float(required=True, allow_none=False, metadata={"title": "Cost Commission Amount", "description": "Cost commission amount from provider", "example": 450.74})
    payment_net = fields.Float(required=True, allow_none=False, metadata={"title": "Net Payment Amount", "description": "Amount to be acquired", "example": 26220})
    fund_amount = fields.Float(required=True, allow_none=False, metadata={"title": "Fund Amount", "description": "Fund amount", "example": 262.2})
    fund_rate = fields.Float(required=True, allow_none=False, metadata={"title": "Fund Rate", "description": "Fund rate", "example": 1})
    prepayment_amount = fields.Float(required=True, allow_none=False, metadata={"title": "Prepayment Amount", "description": "Prepayment amount", "example": 10000})
    installment_count = fields.Integer(required=True, allow_none=False, metadata={"title": "Installment Count", "description": "Installment count", "example": 2})
    installment_plus = fields.Integer(required=True, allow_none=False, metadata={"title": "Plus Installment Count", "description": "Plus installment count", "example": 5})
    installment_amount = fields.Float(required=True, allow_none=False, metadata={"title": "Installment Amount", "description": "Installment amount", "example": 5244})
    installment_description = fields.String(required=True, allow_none=False, metadata={"title": "Installment Description", "description": "Installment description", "example": "2+5 Taksit"})
    card_name = fields.String(required=True, allow_none=False, metadata={"title": "Cardholder Name", "description": "Cardholder name", "example": "John Doe"})
    card_number = fields.String(required=True, allow_none=False, metadata={"title": "Card Number", "description": "Card number", "example": "123456******1234"})
    card_type = fields.String(required=True, allow_none=False, metadata={"title": "Card Type", "description": "Card type", "example": "Troy"})
    card_family = fields.String(required=True, allow_none=False, metadata={"title": "Card Family", "description": "Card family", "example": "Bankkart"})
    campaign_name = fields.String(required=True, allow_none=False, metadata={"title": "Campaign Name", "description": "Name of campaign which is used during payment", "example": "Bol Taksit Kampanyası"})
    pos_name = fields.String(required=True, allow_none=False, metadata={"title": "Virtual PoS Name", "description": "Name of virtual pos which is used as payment provider", "example": "Paylox | Banka"})
    transaction_id = fields.String(required=True, allow_none=False, metadata={"title": "Transaction ID", "description": "Unique transaction number", "example": "a79c480b74181cbc8b95eeed29fdcb3e"})
    transaction_name = fields.String(required=True, allow_none=False, metadata={"title": "Transaction Name", "description": "Unique transaction name", "example": ""})
    partner_name = fields.String(required=True, allow_none=False, metadata={"title": "Partner Name", "description": "Partner name", "example": "Jane Doe"})
    partner_email = fields.String(required=True, allow_none=False, metadata={"title": "Partner Email", "description": "Partner email", "example": "jane@d.oe"})
    partner_phone = fields.String(required=True, allow_none=False, metadata={"title": "Partner Phone", "description": "Partner phone", "example": "+905320000000"})
    partner_address = fields.String(required=True, allow_none=False, metadata={"title": "Partner Address", "description": "Partner address", "example": "İstanbul"})
    ip_address = fields.String(required=True, allow_none=False, metadata={"title": "IP Address", "description": "IP address of payer", "example": "34.221.4.6"})
    url_address = fields.String(required=True, allow_none=False, metadata={"title": "URL Address", "description": "Website address on which payment is made", "example": "https://payment.com/my/payment/"})


class OrderCheckoutPaymentReadInput(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.read.input"
    _inherit = "payment.credential.apikey"

    reference = fields.String(required=True, allow_none=False, metadata={"title": "Payment Reference", "description": "Payment unique reference code", "example": "a39ed9ea-43e6-4fda-b535-28068e889453"})


class OrderCheckoutPaymentReadOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.read.output"
    _inherit = "payment.output"

    payments = fields.List(NestedModel("oco.payment.transaction"), required=True, allow_none=False, metadata={"title": "Payment Transactions", "description": "List of payment transactions"})


class OrderCheckoutPaymentCreate(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.create"
    _inherit = "payment.credential.hash"

    items = fields.List(NestedModel("oco.payment.item"), required=True, allow_none=False, metadata={"title": "Payment List", "description": "List of payment items"})


class OrderCheckoutPaymentResult(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.result"

    vat = fields.String(required=True, metadata={"title": "Vendor VAT", "description": "VAT number of related oco", "example": "12345678912"})
    link = fields.String(metadata={"title": "Vendor Payment Link", "description": "Payment Link URL address of related oco", "example": "https://yourdomain.com/p/8850dd69-4496-45b2-bc13-9b47ad939d81"})


class OrderCheckoutPaymentOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.output"
    _inherit = "payment.output"

    result = fields.List(NestedModel("oco.payment.result"), required=True, metadata={"title": "Result", "description": "Detailed result for related request"})


class OrderCheckoutCampaignPartner(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.campaign.partner"

    vat = fields.String(required=False, allow_none=False, metadata={"title": "Dealer VAT", "description": "VAT number of related partner", "example": "12345678912"})
    ref = fields.String(required=False, allow_none=False, metadata={"title": "Dealer Reference", "description": "Reference of related partner", "example": "D123456789"})


class OrderCheckoutCampaignItem(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.campaign.item"

    partner = NestedModel("oco.campaign.partner", required=True, metadata={"title": "Partner Information", "description": "Either VAT or Reference must be provided"})
    name = fields.String(required=True, allow_none=False, metadata={"title": "Campaign Name", "description": "Name of campaign to be used", "example": "Standard"})


class OrderCheckoutCampaignUpdate(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.campaign.update"
    _inherit = "payment.credential.hash"

    campaigns = fields.List(NestedModel("oco.campaign.item"), required=True, allow_none=False, metadata={"title": "Campaign List", "description": "List of partner-campaign pairs"})


class OrderCheckoutCampaignOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.campaign.output"
    _inherit = "payment.output"


class OrderCheckoutPaymentItemWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "oco.payment.item.webhook"
    _inherit = "system.payment.item.webhook"
