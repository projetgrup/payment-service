# -*- coding: utf-8 -*-

def migrate(cr, version):
    
    cr.execute("""SELECT * FROM res_student_payment_old""")
    result = cr.dictfetchall()
    query = """INSERT INTO payment_item(child_id,parent_id,school_id,class_id,bursary_id,term_id,payment_type_id,amount,paid,paid_amount,installment_count,paid_date,company_id,currency_id,create_uid,create_date,write_uid,write_date) VALUES """
    subquery = []
    for res in result:
        subquery.append("""(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" % (res['student_id'],res['parent_id'],res['school_id'],res['class_id'],res['bursary_id'],res['term_id'],res['payment_type_id'],res['amount'],res['paid'],res['paid_amount'],res['installment_count'],res['paid_date'],res['company_id'],res['currency_id'],res['create_uid'],res['create_date'],res['write_uid'],res['write_date']))
    
    query.append(",".join(subquery))
    cr.execute(query)

    cr.execute("""DROP TABLE res_student_payment_old""")
