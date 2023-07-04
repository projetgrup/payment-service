# -*- coding: utf-8 -*-
from odoo import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _paylox_generate_terms(self, line, ip_address):
        if self.company_id.system:
            return True
        return super()._paylox_generate_terms(line, ip_address)
