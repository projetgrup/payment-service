# -*- coding: utf-8 -*-
from odoo import models, fields

class Company(models.Model):
    _inherit = 'res.company'

    tax_office = fields.Char()
    system = fields.Selection([])
