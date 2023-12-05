# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'website', 'template_id'):
        cr.execute('ALTER TABLE website ADD COLUMN template_id integer')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_ok boolean')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_interval_number'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_interval_number integer')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_interval_type'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_interval_type varchar')
