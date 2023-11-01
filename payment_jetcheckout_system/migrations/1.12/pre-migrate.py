# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_dashboard_button_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_dashboard_button_ok boolean')
        cr.execute('UPDATE res_company SET payment_dashboard_button_ok=TRUE')

    if not column_exists(cr, 'res_company', 'payment_dashboard_button_url'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_dashboard_button_url varchar')
