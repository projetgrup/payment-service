# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_users", "user_type"):
        cr.execute(
            """
            ALTER TABLE res_users
            ADD COLUMN user_type varchar
            """,
        )
