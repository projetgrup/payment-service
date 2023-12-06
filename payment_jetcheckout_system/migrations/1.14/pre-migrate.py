# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'website', 'template_id'):
        cr.execute('ALTER TABLE website ADD COLUMN template_id integer')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_ok boolean')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_day'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_day integer')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_user_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_user_ok boolean')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_team_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_team_ok boolean')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_partner_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_partner_ok boolean')

    if not column_exists(cr, 'res_company', 'payment_page_due_reminder_tag_ok'):
        cr.execute('ALTER TABLE res_company ADD COLUMN payment_page_due_reminder_tag_ok boolean')
