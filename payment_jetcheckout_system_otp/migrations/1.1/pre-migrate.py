# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_company", "otp_redirect_url"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN otp_redirect_url varchar
            """,
        )
