# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, api


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    @api.model
    def cron_sync(self):
        self = self.sudo()
        offset = timedelta(hours=3) # Turkiye Timezone
        now = datetime.now() + offset
        pre = now - timedelta(hours=1)
        for company in self.env['res.company'].search([('system', '!=', False)]):
            hour = company.syncops_cron_sync_item_hour % 24
            time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if pre < time <= now:
                if company.syncops_cron_sync_item and company.syncops_cron_sync_item_subtype:
                    wizard = self.env['syncops.sync.wizard'].create({
                        'type': 'item',
                        'system': company.system,
                        'type_item_subtype': company.syncops_cron_sync_item_subtype,
                    })
                    wizard.with_company(company.id).confirm()
                    wizard.with_company(company.id).with_context(wizard_id=wizard.id).sync()
                    wizard.unlink()
