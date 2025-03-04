# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_page_item_add_desc_numericonly'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_item_add_desc_numericonly boolean')
    if not column_exists(cr, 'res_company', 'payment_page_item_add_desc_unique'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_item_add_desc_unique boolean')
    if not column_exists(cr, 'res_company', 'payment_page_item_add_desc_required'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_item_add_desc_required boolean')
