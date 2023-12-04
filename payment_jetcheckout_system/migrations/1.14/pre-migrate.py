# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'website', 'template_id'):
        cr.execute('ALTER TABLE website ADD COLUMN template_id integer')
