# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AuthSamlAttributeMapping(models.Model):
    _name = "auth.saml.attribute.mapping"
    _description = "SAML2 attribute mapping"

    provider_id = fields.Many2one(
        "auth.saml.provider",
        index=True,
        required=True,
    )
    attribute_name = fields.Char(
        string="IDP Response Attribute",
        required=True,
    )
    field_name = fields.Selection(
        string="Field",
        selection="_field_name_selection",
        required=True,
    )

    @api.model
    def _field_name_selection(self):
        user_fields = self.env["res.users"].fields_get().items()

        def valid_field(f, d):
            return d.get("type") == "char" and not d.get("readonly")

        result = [(f, d.get("string")) for f, d in user_fields if valid_field(f, d)]
        result.sort(key=lambda r: r[1])

        return result
