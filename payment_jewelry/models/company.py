# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])
    jewelry_payment_validity_ok = fields.Boolean(string='Jewelry Payment Validity')
    jewelry_payment_validity_time = fields.Integer(string='Jewelry Payment Validity Time')
