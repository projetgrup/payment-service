# -*- coding: utf-8 -*-
from odoo import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _generate_jetcheckout_terms(self, line, ip_address):
        if self.company_id.system:
            return True
        return super()._generate_jetcheckout_terms(line, ip_address)
