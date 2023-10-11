# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'syncops_payment_page_partner_required'):
        cr.execute('ALTER TABLE res_company ADD COLUMN syncops_payment_page_partner_required boolean')
