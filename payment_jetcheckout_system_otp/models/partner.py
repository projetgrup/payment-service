# -*- coding: utf-8 -*-
from odoo import models


class Partner(models.Model):
    _inherit = 'res.partner'

    def _get_payment_url(self, shorten=False):
        self.ensure_one()
        origin = self.env.context.get('origin')
        if origin == 'otp' and self.is_portal:
            return super(Partner, self.with_context(active_type='page'))._get_payment_url(shorten=shorten)
        return super(Partner, self)._get_payment_url(shorten=shorten)
