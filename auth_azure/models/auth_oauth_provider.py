# -*- coding: utf-8 -*-
from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    client_secret_id = fields.Char(string='Client Secret')
    azure_tenant_id = fields.Char(string='Azure Tenant ID')
    response_type = fields.Selection([
        ('token', 'Token'),
        ('code', 'Code')
    ], default='token', string='Response Type')
