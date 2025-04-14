# -*- coding: utf-8 -*-

from odoo import fields, models
from .ir_config_parameter import ALLOW_SAML_UID_AND_PASSWORD


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allow_saml_uid_and_internal_password = fields.Boolean("Allow SAML users to possess a password", config_parameter=ALLOW_SAML_UID_AND_PASSWORD)
