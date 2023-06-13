# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if column_exists(cr, "res_company", "required_2fa"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN required_2fa boolean
            """,
        )
