# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists


def migrate(cr, version):
    if not column_exists(cr, 'res_partner', 'can_approve_payment_plan'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN can_approve_payment_plan boolean')
    if not column_exists(cr, 'res_company', 'payment_plan_approver_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_plan_approver_ok boolean')
