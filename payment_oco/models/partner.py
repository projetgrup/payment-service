# -*- coding: utf-8 -*-
from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    system = fields.Selection(selection_add=[('oco', 'Order Checkout')])

    def action_payable(self):
        action = super(Partner, self).action_payable()
        system = self.company_id and self.company_id.system or self.env.context.get('active_system')
        if system == 'oco':
            action['context']['domain'] = self.ids
        return action
