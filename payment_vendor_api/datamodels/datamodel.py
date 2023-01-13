# -*- coding: utf-8 -*-
from marshmallow import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class VendorItemInput(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.item.input"

    response_code = fields.Integer(required=True, allow_none=False, title="Response Code", description="Integer which is returned to represent response", example=0)
    response_message = fields.String(required=True, allow_none=False, title="Response Message", description="Description which is returned to represent response", example="Success")


class VendorItemOutput(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.item.output"
    _inherit = "payment.output"


class VendorWebhook(Datamodel):
    class Meta:
        ordered = True

    _name = "vendor.webhook"
    _inherit = "system.webhook"
