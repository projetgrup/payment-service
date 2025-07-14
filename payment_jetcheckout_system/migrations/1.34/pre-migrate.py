# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_partner', 'is_subpartner'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN is_subpartner boolean')
    if not column_exists(cr, 'res_partner', 'use_subpartner'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN use_subpartner boolean')
