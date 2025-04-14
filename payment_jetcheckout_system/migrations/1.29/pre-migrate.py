# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_einvoice_identifier'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_einvoice_identifier varchar')
    if not column_exists(cr, 'res_company', 'payment_page_amount_editable_wo_exceed'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_amount_editable_wo_exceed boolean')
