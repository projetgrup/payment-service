# -- coding: utf-8 --
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

import os
import base64
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class IrDefault(models.Model):
    _inherit = 'ir.default'

    @api.model
    def set_whitelabel_favicon(self, model, field):
        script_dir = os.path.dirname(__file__)
        rel_path = "../static/src/img/favicon.png"
        abs_file_path = os.path.join(script_dir, rel_path)
        with open(abs_file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            self.set('res.config.settings', 'whitelabel_favicon', encoded_string.decode("utf-8"))
