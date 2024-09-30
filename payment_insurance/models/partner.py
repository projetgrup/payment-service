# -*- coding: utf-8 -*-
from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    system = fields.Selection(selection_add=[('insurance', 'Insurance Payment System')])

    def action_payable(self):
        action = super(Partner, self).action_payable()
        system = self.company_id and self.company_id.system or self.env.context.get('active_system')
        if system == 'insurance':
            action['context']['domain'] = self.ids
        return action
