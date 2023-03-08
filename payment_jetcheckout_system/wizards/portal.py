# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    @api.model
    def default_get(self, fields):
        partner_ids = self.env.context.get('default_partner_ids', []) or self.env.context.get('active_ids', [])
        partners = self.env['res.partner'].sudo().browse(partner_ids)
        if self.env.company.system or any(partner.system for partner in partners):
            raise UserError(_('Please use "Grant Access" button to get this feature'))
        return super(PortalWizard, self).default_get(fields)


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    def _send_email(self):
        return super(PortalWizardUser, self.sudo())._send_email()
