# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_company", "system_product_payment_validity_ok"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN system_product_payment_validity_ok boolean
            """,
        )

    if not column_exists(cr, "res_company", "system_product_payment_validity_time"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN system_product_payment_validity_time integer
            """,
        )
