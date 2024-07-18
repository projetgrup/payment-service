# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_company", "api_item_new_data_only"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN api_item_new_data_only boolean
            """,
        )
