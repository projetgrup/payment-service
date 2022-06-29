# -*- coding: utf-8 -*-
from odoo import models, api


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    def _send_email(self):
        return super(PortalWizardUser, self.sudo())._send_email()
