# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("UPDATE payment_transaction SET jetcheckout_payment_type='virtualpos' WHERE jetcheckout_payment_type='virtual_pos'")
    cr.execute("UPDATE payment_transaction SET jetcheckout_payment_type='physicalpos' WHERE jetcheckout_payment_type='physical_pos'")
    cr.execute("UPDATE payment_transaction SET jetcheckout_payment_type='softpos' WHERE jetcheckout_payment_type='soft_pos'")
