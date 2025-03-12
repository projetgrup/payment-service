# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("UPDATE payment_hook SET subtype = 'transaction_create' WHERE type = 'transaction' AND subtype = 'create'")
    cr.execute("UPDATE payment_hook SET subtype = 'transaction_finalize' WHERE type = 'transaction' AND subtype = 'finalize'")
    cr.execute("UPDATE payment_hook SET subtype = 'item_create' WHERE type = 'item' AND subtype = 'create'")
    cr.execute("UPDATE payment_hook SET subtype = 'item_finalize' WHERE type = 'item' AND subtype = 'finalize'")
