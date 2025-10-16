# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("UPDATE payment_transaction_basket SET ad_state='transferred' WHERE ad_state='sold'")
