# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResUserSaml(models.Model):
    _name = "res.users.saml"
    _description = "User to SAML Provider Mapping"

    user_id = fields.Many2one("res.users", index=True, required=True, ondelete='cascade')
    saml_uid = fields.Char("SAML User ID", required=True)
    saml_access_token = fields.Char("Current SAML token for this user")
    saml_provider_id = fields.Many2one("auth.saml.provider", string="SAML Provider", index=True)

    _sql_constraints = [
        (
            "uniq_users_saml_provider_saml_uid",
            "unique(saml_provider_id, saml_uid)",
            "SAML UID must be unique per provider",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        if not self.env["res.users"].allow_saml_and_password():
            result.mapped("user_id").write({"password": False})
        return result
