# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("UPDATE product_product SET escrow_state='transferred' WHERE escrow_state='sold'")
