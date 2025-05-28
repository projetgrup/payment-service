# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_page_init_warning_commission_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_init_warning_commission_ok boolean')
    if not column_exists(cr, 'res_company', 'payment_page_init_warning_commission_show_rate'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_init_warning_commission_show_rate boolean')
    if not column_exists(cr, 'res_company', 'payment_page_init_warning_commission_show_primary_advice'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_init_warning_commission_show_primary_advice boolean')
    if not column_exists(cr, 'res_company', 'payment_page_init_warning_commission_show_secondary_advice'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_init_warning_commission_show_secondary_advice boolean')
    if not column_exists(cr, 'res_company', 'payment_page_init_warning_commission_show_calculation'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_init_warning_commission_show_calculation boolean')
    if not column_exists(cr, 'res_company', 'payment_page_init_warning_commission_description'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_init_warning_commission_description text')
