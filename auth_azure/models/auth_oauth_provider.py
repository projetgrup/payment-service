# -*- coding: utf-8 -*-
from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    client_secret_id = fields.Char(string='Client Secret')
    response_type = fields.Selection([('token', 'Token'), ('code', 'Code')], default='token', required=True, String="Response Type")
