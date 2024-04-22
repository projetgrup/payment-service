# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    system_product = fields.Boolean(string='Products')
    system_product_payment_validity_ok = fields.Boolean(string='Payment Validity')
    system_product_payment_validity_time = fields.Integer(string='Payment Validity Time')

    def _update_system_product(self):
        group = self.env.ref('payment_system_product.group_product')
        for company in self:
            users = self.env['res.users'].sudo().with_context(active_test=False).search([
                ('share', '=', False),
                ('company_id', '=', company.id),
            ])
            code = company.system_product and 4 or 3
            users.write({'groups_id': [(code, group.id)]})

    @api.model
    def create(self, values):
        res = super().create(values)
        if 'system_product' in values:
            res._update_system_product()
        return res

    def write(self, values):
        res = super().write(values)
        if 'system_product' in values:
            self._update_system_product()
        return res
