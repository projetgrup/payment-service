# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_transaction_export_txt_cron_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_transaction_export_txt_cron_ok boolean')
    if not column_exists(cr, 'res_company', 'payment_transaction_export_txt_cron_hour'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_transaction_export_txt_cron_hour integer')
