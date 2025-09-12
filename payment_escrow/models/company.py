# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    conveyance_show_link = fields.Boolean(string='Enable Conveyance Document Show Link', default=False)
