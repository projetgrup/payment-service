# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists


def migrate(cr, version):
    for (old, new) in [('payment_student.group_sps_user', 'payment_student.group_student_user'), ('payment_student.group_sps_manager', 'payment_student.group_student_manager')]:
        cr.execute(
            """
            UPDATE ir_model_data SET module = %s, name = %s
            WHERE module = %s and name = %s
            """, tuple(new.split('.') + old.split('.'))
        )

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

    cr.execute("""SELECT * FROM res_student_setting""")
    result = cr.dictfetchall()
    for res in result:
        company = res['company_id']
        cr.execute(
            """
            UPDATE res_company SET
            student_discount_sibling_active = %s,
            student_discount_advance_active = %s,
            student_discount_sibling_maximum = %s
            student_discount_sibling_rate = %s,
            WHERE id = %s
            """, tuple(res['is_discount_sibling'], res['is_discount_advance'], res['discount_maximum'], res['discount_sibling'], company)
        )
        cr.execute(
            """
            UPDATE website SET
            payment_footer = %s,
            payment_privacy_policy = %s,
            payment_sale_agreement = %s
            payment_membership_agreement = %s,
            payment_contact_page = %s,
            WHERE company_id = %s
            """, tuple(res['website_footer'], res['privacy_policy'], res['sale_agreement'], res['membership_agreement'], res['contact_page'], company)
        )

    cr.execute("""SELECT * FROM res_student_payment""")
    result = cr.dictfetchall()
    query = """INSERT INTO payment_item(child_id,parent_id,school_id,class_id,bursary_id,term_id,payment_type_id,amount,paid,paid_amount,installment_count,paid_date,company_id,currency_id,create_uid,create_date,write_uid,write_date) VALUES """
    subquery = []
    for res in result:
        subquery.append("""(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" % (res['student_id'],res['parent_id'],res['school_id'],res['class_id'],res['bursary_id'],res['term_id'],res['payment_type_id'],res['amount'],res['paid'],res['paid_amount'],res['installment_count'],res['paid_date'],res['company_id'],res['currency_id'],res['create_uid'],res['create_date'],res['write_uid'],res['write_date']))
    
    query.append(",".join(subquery))
    cr.execute(query)
