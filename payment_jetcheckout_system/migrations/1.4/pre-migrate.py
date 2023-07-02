# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_company", "notif_mail_success_ok"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN notif_mail_success_ok boolean
            """,
        )

    if not column_exists(cr, "res_company", "notif_sms_success_ok"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN notif_sms_success_ok boolean
            """,
        )
