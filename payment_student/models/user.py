# -*- coding: utf-8 -*-
from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, values):
        res = super().create(values)
        if 'company_id' in values:
            res.company_id._update_system_student_type()
        return res

    def write(self, values):
        res = super().write(values)
        if 'company_id' in values:
            self.mapped('company_id')._update_system_student_type()
        return res
