# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    syncops_sync_item_force = fields.Boolean(related='company_id.syncops_sync_item_force', readonly=False)
    syncops_cron_sync_partner = fields.Boolean(related='company_id.syncops_cron_sync_partner', readonly=False)
    syncops_payment_page_partner_required = fields.Boolean(related='company_id.syncops_payment_page_partner_required', readonly=False)
