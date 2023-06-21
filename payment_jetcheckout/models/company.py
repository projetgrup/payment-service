# -*- coding: utf-8 -*-
from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    payment_page_campaign_table_ok = fields.Boolean('Campaign Table on Payment Page')
