# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_partner_unique_field'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_partner_unique_field varchar')
        cr.execute("UPDATE res_company SET payment_partner_unique_field='vat'")
