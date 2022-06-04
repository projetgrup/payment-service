# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError

class Company(models.Model):
    _inherit = 'res.company'

    tax_office = fields.Char()
    system = fields.Selection([])
