# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_company", "payment_page_campaign_table_transpose"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN payment_page_campaign_table_transpose boolean
            """,
        )
