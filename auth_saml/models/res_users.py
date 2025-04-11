# -*- coding: utf-8 -*-

import passlib
import random
import logging

from typing import Set

from odoo import SUPERUSER_ID, _, api, fields, models, registry, tools
from odoo.exceptions import AccessDenied, ValidationError

from .ir_config_parameter import ALLOW_SAML_UID_AND_PASSWORD

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    _inherit = "res.users"

    saml_ids = fields.One2many("res.users.saml", "user_id")

    def _auth_saml_validate(self, provider_id: int, token: str, base_url: str = None):
        provider = self.env["auth.saml.provider"].sudo().browse(provider_id)
        return provider._validate_auth_response(token, base_url)

    def _auth_saml_signin(self, provider: int, validation: dict, saml_response) -> str:
        saml_uid = validation["user_id"]
        user_saml = self.env["res.users.saml"].search([
            ("saml_uid", "=", saml_uid),
            ("saml_provider_id", "=", provider)
        ], limit=1)
        if user_saml:
            user = user_saml.user_id
        else:
            s = "abcdefghijklmnopqrstuvwxyz034567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
            user = self.env['res.users'].sudo()._create_user_from_template({
                'name': saml_uid,
                'login': saml_uid,
                'password': ''.join(random.sample(s, 16)),
                'company_id': self.env.company.id,
            })
            user_saml = self.env['res.users.saml'].sudo().create({
                'user_id': user.id,
                'saml_uid': saml_uid,
                'saml_provider_id': provider,
            })
            user.with_user(user)._update_last_login()

        if len(user) != 1:
            raise AccessDenied()

        with registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            user_saml.with_env(new_env).write({"saml_access_token": saml_response})

        if validation.get("mapped_attrs", {}):
            user.write(validation.get("mapped_attrs", {}))

        return user.login

    @api.model
    def auth_saml(self, provider: int, saml_response: str, base_url: str = None):
        validation = self._auth_saml_validate(provider, saml_response, base_url)
        if not validation.get("user_id"):
            raise AccessDenied()

        login = self._auth_saml_signin(provider, validation, saml_response)
        if not login:
            raise AccessDenied()

        return self.env.cr.dbname, login, saml_response

    def _check_credentials(self, password, env):
        try:
            return super()._check_credentials(password, env)

        except (AccessDenied, passlib.exc.PasswordSizeError):
            token = (
                self.env["res.users.saml"].sudo().search([
                    ("user_id", "=", self.env.user.id),
                    ("saml_access_token", "=", password),
                ])
            )
            if token:
                return
            raise AccessDenied() from None

    @api.model
    def _saml_allowed_user_ids(self) -> Set[int]:
        allowed_users = {SUPERUSER_ID}
        user_admin = self.env.ref("base.user_admin", False)
        if user_admin:
            allowed_users.add(user_admin.id)
        return allowed_users

    @api.model
    def allow_saml_and_password(self) -> bool:
        return tools.str2bool(self.env["ir.config_parameter"].sudo().get_param(ALLOW_SAML_UID_AND_PASSWORD))

    def _set_password(self):
        if not self.allow_saml_and_password():
            saml_users = self.filtered(
                lambda user: user.sudo().saml_ids
                and user.id not in self._saml_allowed_user_ids()
                and user.password
            )
            if saml_users:
                raise ValidationError(
                    _(
                        "This database disallows users to "
                        "have both passwords and SAML IDs. "
                        "Error for logins %s"
                    )
                    % saml_users.mapped("login")
                )
        blank_password_users = self.filtered(lambda user: user.password is False)
        non_blank_password_users = self - blank_password_users
        if non_blank_password_users:
            super(ResUser, non_blank_password_users)._set_password()
        if blank_password_users:
            self.env.cr.execute(
                "UPDATE res_users SET password = NULL WHERE id IN %s",
                (tuple(blank_password_users.ids),),
            )
            self.invalidate_cache(["password"], blank_password_users.ids)
        return

    def allow_saml_and_password_changed(self):
        if not self.allow_saml_and_password():
            users_to_blank_password = self.sudo().search([
                "&",
                ("saml_ids", "!=", False),
                ("id", "not in", list(self._saml_allowed_user_ids())),
            ])
            _logger.debug("Removing password from %s user(s)", len(users_to_blank_password))
            users_to_blank_password.write({"password": False})
