# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_partner', 'syncops_ok'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN syncops_ok boolean')
    if not column_exists(cr, 'res_partner', 'syncops_ref'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN syncops_ref varchar')
    if not column_exists(cr, 'res_partner', 'syncops_state'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN syncops_state boolean')
    if not column_exists(cr, 'res_partner', 'syncops_state_message'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN syncops_state_message text')
