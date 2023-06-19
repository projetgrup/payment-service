# -*- coding: utf-8 -*-
from odoo import models, fields

import odoo
from odoo.tools.sql import column_exists

try:
    registry = odoo.registry('jettahsilat')
    with registry.cursor() as cr:
        if not column_exists(cr, "res_company", "payment_page_campaign_table_ok"):
            cr.execute("ALTER TABLE res_company ADD COLUMN payment_page_campaign_table_ok boolean")
except:
    pass

class Company(models.Model):
    _inherit = 'res.company'

    payment_page_campaign_table_ok = fields.Boolean('Campaign Table on Payment Page')
