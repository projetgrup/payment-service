# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('insurance', 'Insurance Payment System')])
