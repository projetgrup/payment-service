# -*- coding: utf-8 -*-

from odoo import api, models

ALLOW_SAML_UID_AND_PASSWORD = "auth_saml.allow_saml_uid_and_internal_password"


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        if result.filtered(lambda param: param.key == ALLOW_SAML_UID_AND_PASSWORD):
            self.env["res.users"].allow_saml_and_password_changed()
        return result

    def write(self, vals):
        result = super().write(vals)
        if self.filtered(lambda param: param.key == ALLOW_SAML_UID_AND_PASSWORD):
            self.env["res.users"].allow_saml_and_password_changed()
        return result

    def unlink(self):
        param_saml = self.filtered(
            lambda param: param.key == ALLOW_SAML_UID_AND_PASSWORD
        )
        result = super().unlink()
        if result and param_saml:
            self.env["res.users"].allow_saml_and_password_changed()
        return result
