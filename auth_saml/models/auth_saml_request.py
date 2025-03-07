# -*- coding: utf-8 -*-

from odoo import fields, models


class AuthSamlRequest(models.TransientModel):
    _name = "auth_saml.request"
    _description = "SAML Outstanding Requests"
    _rec_name = "saml_request_id"

    saml_provider_id = fields.Many2one(
        "auth.saml.provider",
        string="SAML Provider that issued the token",
        required=True,
    )
    saml_request_id = fields.Char(
        "Current Request ID",
        required=True,
    )
