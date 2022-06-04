# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, "res_company", "tax_office"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN tax_office varchar
            """,
        )
    if not column_exists(cr, "res_company", "system"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN system varchar
            """,
        )
    if not column_exists(cr, "website", "payment_footer"):
        cr.execute(
            """
            ALTER TABLE website
            ADD COLUMN payment_footer text
            """,
        )
    if not column_exists(cr, "website", "payment_privacy_policy"):
        cr.execute(
            """
            ALTER TABLE website
            ADD COLUMN payment_privacy_policy text
            """,
        )
    if not column_exists(cr, "website", "payment_sale_agreement"):
        cr.execute(
            """
            ALTER TABLE website
            ADD COLUMN payment_sale_agreement text
            """,
        )
    if not column_exists(cr, "website", "payment_membership_agreement"):
        cr.execute(
            """
            ALTER TABLE website
            ADD COLUMN payment_membership_agreement text
            """,
        )
    if not column_exists(cr, "website", "payment_contact_page"):
        cr.execute(
            """
            ALTER TABLE website
            ADD COLUMN payment_contact_page text
            """,
        )
