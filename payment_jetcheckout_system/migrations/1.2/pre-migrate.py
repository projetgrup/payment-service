# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if column_exists(cr, "payment_item", "system"):
        cr.execute(
            """
            ALTER TABLE payment_item
            ADD COLUMN system_temp varchar
            """,
        )
        cr.execute(
            """
            UPDATE payment_item
            SET system_temp = system
            """,
        )
