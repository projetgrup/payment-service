# -- coding: utf-8 --
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        domain += [("to_buy", "=", False)]
        return super().search(domain, offset, limit, order, count)
