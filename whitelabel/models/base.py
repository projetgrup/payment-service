# -- coding: utf-8 --
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        res = super().search(domain, offset, limit, order, count)
        if self._name == "payment.acquirer":
            try:
                res = res.filtered(lambda a: not a.module_to_buy)
            except:
                pass
        return res
