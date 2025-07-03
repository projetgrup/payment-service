# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'syncops_payment_page_repull_partners'):
        cr.execute('ALTER TABLE res_company ADD COLUMN syncops_payment_page_repull_partners boolean')
        cr.execute('UPDATE res_company SET syncops_payment_page_repull_partners=true')
