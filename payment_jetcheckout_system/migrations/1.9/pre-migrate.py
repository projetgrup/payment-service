# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_page_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_ok boolean')

    if not column_exists(cr, 'res_users', 'payment_page_ok'):
        cr.execute('ALTER TABLE res_users ADD COLUMN payment_page_ok boolean')
