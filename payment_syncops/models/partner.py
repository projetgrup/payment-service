# -*- coding: utf-8 -*-
from odoo import models, api


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def cron_sync(self):
        self = self.sudo()
        for company in self.env['res.company'].search([]):
            if company.syncops_cron_sync_partner:
                wizard = self.env['syncops.sync.wizard'].create({
                    'type': 'partner',
                    'system': company.system,
                })
                wizard.with_company(company.id).confirm()
                wizard.with_company(company.id).with_context(wizard_id=wizard.id).sync()
                wizard.unlink()
