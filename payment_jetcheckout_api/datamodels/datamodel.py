# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
#from odoo.addons.datamodel.fields import NestedModel

class PaymentResponse(Datamodel):
    _name = "payment.response"

    response_code = fields.Integer(required=True, allow_none=False)
    response_message = fields.String(required=True, allow_none=False)

class PaymentApi(Datamodel):
    _name = "payment.api"

    application_key = fields.String(required=True, allow_none=False)

class PaymentApiSecret(Datamodel):
    _name = "payment.api.secret"
    _inherit = "payment.api"

    secret_key = fields.String(required=True, allow_none=False)

class PaymentResultInput(Datamodel):
    _name = "payment.result.input"
    _inherit = "payment.api"

    hash = fields.String(required=True, allow_none=False)

class PaymentPrepareInput(Datamodel):
    _name = "payment.prepare.input"
    _inherit = "payment.api"

    amount = fields.Float(required=True, allow_none=False)
    id = fields.Integer(required=True, allow_none=False)
    hash = fields.String(required=True, allow_none=False)
    customer = fields.Dict(required=True, allow_none=False)
    order = fields.Dict(required=True, allow_none=False)
    product = fields.Dict(required=True, allow_none=False)
    return_url = fields.String(required=True, allow_none=False)

class PaymentPrepareOutput(Datamodel):
    _name = "payment.prepare.output"
    _inherit = "payment.response"

    hash = fields.String(required=False, allow_none=False)

class PaymentResultOutput(Datamodel):
    _name = "payment.result.output"
    _inherit = "payment.response"

    provider = fields.String(required=False, allow_none=False)
    state = fields.String(required=False, allow_none=False)
    fees = fields.Float(required=False, allow_none=False)
    ip_address = fields.String(required=False, allow_none=False)
    card_name = fields.String(required=False, allow_none=False)
    card_number = fields.String(required=False, allow_none=False)
    card_type = fields.String(required=False, allow_none=False)
    vpos_name = fields.String(required=False, allow_none=False)
    order_id = fields.String(required=False, allow_none=False)
    transaction_id = fields.String(required=False, allow_none=False)
    payment_amount = fields.Float(required=False, allow_none=False)
    installment_count = fields.Integer(required=False, allow_none=False)
    installment_amount = fields.Float(required=False, allow_none=False)
    commission_rate = fields.Float(required=False, allow_none=False)
    commission_amount = fields.Float(required=False, allow_none=False)
    customer_rate = fields.Float(required=False, allow_none=False)
    customer_amount = fields.Float(required=False, allow_none=False)
