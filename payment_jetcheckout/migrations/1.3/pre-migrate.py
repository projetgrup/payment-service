# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_partner", "campaign_id"):
        cr.execute(
            """
            ALTER TABLE res_partner
            ADD COLUMN campaign_id integer
            """,
        )
