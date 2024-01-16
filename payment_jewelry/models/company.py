# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])
