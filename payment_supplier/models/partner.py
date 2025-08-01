# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    system = fields.Selection(selection_add=[('supplier', 'Supplier Payment System')])

    def action_payable(self):
        action = super(Partner, self).action_payable()
        system = self.company_id and self.company_id.system or self.env.context.get('active_system')
        if system == 'supplier':
            action['context']['domain'] = self.ids
        return action

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('default_can_approve_payment_plan'):
            res['parent_id'] = self.env.company.partner_id.id
        return res
