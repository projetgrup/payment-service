# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    syncops_sync_item_force = fields.Boolean(related='company_id.syncops_sync_item_force', readonly=False)
    syncops_cron_sync_partner = fields.Boolean(related='company_id.syncops_cron_sync_partner', readonly=False)
    syncops_payment_page_partner_required = fields.Boolean(related='company_id.syncops_payment_page_partner_required', readonly=False)
    syncops_cron_sync_item = fields.Boolean(related='company_id.syncops_cron_sync_item', readonly=False)
    syncops_cron_sync_item_subtype = fields.Selection(related='company_id.syncops_cron_sync_item_subtype', readonly=False)
    syncops_cron_sync_item_hour = fields.Integer(related='company_id.syncops_cron_sync_item_hour', readonly=False)

    @api.onchange('syncops_cron_sync_item_hour')
    def onchange_syncops_cron_sync_item_hour(self):
        if self.syncops_cron_sync_item_hour >= 24:
            self.syncops_cron_sync_item_hour %= 24
