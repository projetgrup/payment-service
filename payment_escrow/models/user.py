# -*- coding: utf-8 -*-
from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _is_restricted_escrow_user(self):
        self.ensure_one()
        return self.has_group('payment_escrow.group_escrow_user') and not self.has_group('payment_escrow.group_escrow_manager')

    def _get_escrow_allowed_type_map(self):
        self.ensure_one()
        company_map = {}
        for company in self.company_ids:
            if company.system != 'escrow':
                continue
            allowed = company._get_escrow_allowed_types_for_user(self)
            if allowed:
                company_map[company.id] = allowed
        return company_map
