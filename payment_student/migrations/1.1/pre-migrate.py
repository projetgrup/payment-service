# -*- coding: utf-8 -*-
import logging
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""SELECT 1 FROM ir_module_module WHERE name = 'payment_jetcheckout_system' and state = 'installed'""")
    result = cr.fetchone()
    if not result:
        raise Exception('You cannot upgrade this module, you must install module "payment_jetcheckout_system" first.')

    if not column_exists(cr, "res_company", "student_discount_sibling_active"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN student_discount_sibling_active boolean
            """,
        )

    if not column_exists(cr, "res_company", "student_discount_advance_active"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN student_discount_advance_active boolean
            """,
        )

    if not column_exists(cr, "res_company", "student_discount_sibling_maximum"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN student_discount_sibling_maximum boolean
            """,
        )

    if not column_exists(cr, "res_company", "student_discount_sibling_rate"):
        cr.execute(
            """
            ALTER TABLE res_company
            ADD COLUMN student_discount_sibling_rate numeric
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
    try:
        cr.execute(
            """
            UPDATE ir_model_data SET name = 'group_student_user'
            WHERE module = 'payment_student' and name = 'group_sps_user'
            """
        )
        cr.execute(
            """
            UPDATE ir_model_data SET name = 'group_student_manager'
            WHERE module = 'payment_student' and name = 'group_sps_manager'
            """
        )

        cr.execute("""SELECT * FROM res_student_setting""")
        result = cr.dictfetchall()
        for res in result:
            company = res['company_id']
            cr.execute(
                f"""
                UPDATE res_company SET
                student_discount_sibling_active = {res['is_discount_sibling']},
                student_discount_advance_active = {res['is_discount_advance']},
                student_discount_sibling_maximum = {res['discount_maximum']},
                student_discount_sibling_rate = {res['discount_sibling']}
                WHERE id = {company}
                """
            )
            cr.execute(
                f"""
                UPDATE website SET
                payment_footer = '{res['website_footer']}',
                payment_privacy_policy = '{res['privacy_policy']}',
                payment_sale_agreement = '{res['sale_agreement']}',
                payment_membership_agreement = '{res['membership_agreement']}',
                payment_contact_page = '{res['contact_page']}'
                WHERE company_id = {company}
                """
            )

        cr.execute("""DROP TABLE payment_item CASCADE""")
        cr.execute("""DROP TABLE transaction_item_rel CASCADE""")
        cr.execute("""ALTER TABLE res_student_payment RENAME TO payment_item""")
        cr.execute("""ALTER TABLE payment_item RENAME COLUMN student_id TO child_id""")
        cr.execute("""ALTER SEQUENCE res_student_payment_id_seq RENAME TO payment_item_id_seq""")
        cr.execute("""ALTER INDEX res_student_payment_pkey RENAME TO payment_item_pkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_bursary_id_fkey TO payment_item_bursary_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_class_id_fkey TO payment_item_class_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_company_id_fkey TO payment_item_company_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_create_uid_fkey TO payment_item_create_uid_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_currency_id_fkey TO payment_item_currency_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_parent_id_fkey TO payment_item_parent_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_payment_type_id_fkey TO payment_item_payment_type_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_school_id_fkey TO payment_item_school_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_student_id_fkey TO payment_item_student_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_term_id_fkey TO payment_item_term_id_fkey""")
        cr.execute("""ALTER TABLE payment_item RENAME CONSTRAINT res_student_payment_write_uid_fkey TO payment_item_write_uid_fkey""")
        cr.execute("""ALTER TABLE transaction_payment_rel RENAME TO transaction_item_rel""")
        cr.execute("""ALTER TABLE transaction_item_rel RENAME COLUMN payment_id TO item_id""")
        cr.execute("""ALTER TABLE transaction_item_rel RENAME CONSTRAINT transaction_payment_rel_payment_id_fkey TO transaction_item_rel_item_id_fkey""")
        cr.execute("""DROP TABLE res_student_setting CASCADE""")
    except Exception as e:
        _logger.error(str(e))
        raise
