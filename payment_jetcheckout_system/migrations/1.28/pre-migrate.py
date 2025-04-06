# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_company', 'payment_plan_threed_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_plan_threed_ok boolean')
    if not column_exists(cr, 'res_company', 'payment_plan_fullscreen_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_plan_fullscreen_ok boolean')
