# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if column_exists(cr, "payment_item", "system_temp"):
        cr.execute(
            """
            UPDATE payment_item
            SET system = system_temp
            """,
        )
        cr.execute(
            """
            ALTER TABLE payment_item
            DROP COLUMN  system_temp
            """,
        )
