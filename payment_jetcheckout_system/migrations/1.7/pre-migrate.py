# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_page_due_hide_payment_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_hide_payment_ok boolean')

    if not column_exists(cr, 'res_company', 'payment_page_due_hide_payment_message'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_hide_payment_message text')

    if not column_exists(cr, 'res_company', 'payment_page_item_priority'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_item_priority boolean')

    if not column_exists(cr, 'res_users', 'payment_page_item_priority'):
        cr.execute('ALTER TABLE res_users ADD COLUMN payment_page_item_priority boolean')
