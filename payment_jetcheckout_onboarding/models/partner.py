# -*- coding: utf-8 -*-
from odoo import models

class Partner(models.Model):
    _inherit = 'res.partner'

    def signup_cancel(self):
        return super(Partner, self.sudo()).signup_cancel()
