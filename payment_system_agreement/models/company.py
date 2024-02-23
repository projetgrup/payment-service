# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    system_agreement = fields.Boolean(string='Agreements')

    def _update_system_agreement(self):
        group = self.env.ref('payment_system_agreement.group_agreement')
        for company in self:
            users = self.env['res.users'].sudo().with_context(active_test=False).search([
                ('share', '=', False),
                ('company_id', '=', company.id),
            ])
            code = company.system_agreement and 4 or 3
            users.write({'groups_id': [(code, group.id)]})

    @api.model
    def create(self, values):
        res = super().create(values)
        res._update_system_agreement()
        return res

    def write(self, values):
        res = super().write(values)
        self._update_system_agreement()
        return res
