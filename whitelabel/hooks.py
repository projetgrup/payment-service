# -- coding: utf-8 --
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, api
from odoo.tools import config


def post_init_hook(cr, registry):
    if config["test_enable"] or config["test_file"]:
        with api.Environment.manage():
            env = api.Environment(cr, SUPERUSER_ID, {})
            env.ref("whitelabel.layout_footer_copyright").active = False

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        env['ir.config_parameter'].sudo().set_param('report.url', 'http://127.0.0.1:8069')
