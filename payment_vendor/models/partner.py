# -*- coding: utf-8 -*-
from odoo import models, fields

class Partner(models.Model):
    _inherit = 'res.partner'

    system = fields.Selection(selection_add=[('vendor', 'Vendor Payment System')])

    def action_payable(self):
        action = super(Partner, self).action_payable()
        system = self.company_id and self.company_id.system or self.env.context.get('active_system')
        if system == 'vendor':
            action['context']['domain'] = self.ids
        return action

    def _get_payment_url(self, shorten=False):
        self.ensure_one()
        origin = self.env.context.get('origin')
        if origin == 'otp' and self.is_portal:
            return super(Partner, self.with_context(active_type='page'))._get_payment_url(shorten=shorten)
        return super(Partner, self)._get_payment_url(shorten=shorten)
