# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    tax_office = fields.Char('Tax Office')
    usage_type = fields.Selection([('retailer','Retailer Payment System'), ('student','Student Payment System')], 'Usage Type')
