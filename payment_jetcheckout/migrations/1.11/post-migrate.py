# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("UPDATE payment_plan SET installment_id = installment_count")
