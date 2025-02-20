# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if column_exists(cr, 'payment_agreement', 'required'):
        cr.execute("UPDATE payment_agreement SET required = TRUE")
