# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'syncops_sync_item_force'):
        cr.execute('ALTER TABLE res_company ADD COLUMN syncops_sync_item_force boolean')

    if not column_exists(cr, 'res_company', 'syncops_cron_sync_item'):
        cr.execute('ALTER TABLE res_company ADD COLUMN syncops_cron_sync_item boolean')

    if not column_exists(cr, 'res_company', 'syncops_cron_sync_item_subtype'):
        cr.execute('ALTER TABLE res_company ADD COLUMN syncops_cron_sync_item_subtype varchar')

    if not column_exists(cr, 'res_company', 'syncops_cron_sync_item_hour'):
        cr.execute('ALTER TABLE res_company ADD COLUMN syncops_cron_sync_item_hour integer')
