# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    syncops_sync_item_subtype = fields.Char()
    syncops_sync_item_force = fields.Boolean()
    syncops_cron_sync_item = fields.Boolean()
    syncops_cron_sync_item_subtype = fields.Selection([('balance', 'Current Balances'), ('invoice', 'Unpaid Invoices')])
    syncops_cron_sync_item_hour = fields.Integer()
    syncops_cron_sync_partner = fields.Boolean()
    syncops_payment_page_partner_required = fields.Boolean()
