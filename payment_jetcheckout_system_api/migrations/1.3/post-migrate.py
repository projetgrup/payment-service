# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if column_exists(cr, "payment_acquirer_jetcheckout_api", "perm_payment"):
        cr.execute("UPDATE payment_acquirer_jetcheckout_api SET perm_payment = TRUE")
