# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_company", "api_item_notif_mail_create_filter_email"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN api_item_notif_mail_create_filter_email text
            """,
        )
    if not column_exists(cr, "res_company", "api_item_notif_mail_create_filter_email_ok"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN api_item_notif_mail_create_filter_email_ok boolean
            """,
        )
    if not column_exists(cr, "res_company", "api_item_notif_sms_create_filter_number"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN api_item_notif_sms_create_filter_number text
            """,
        )
    if not column_exists(cr, "res_company", "api_item_notif_sms_create_filter_number_ok"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN api_item_notif_sms_create_filter_number_ok boolean
            """,
        )
