# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    conveyance_show_link = fields.Boolean(string='Enable Conveyance Document Show Link', default=False)
    broker_registration_enabled = fields.Boolean('Enable Broker Registration', default=False)
    dealer_registration_enabled = fields.Boolean('Enable Dealer Registration', default=False)
    escrow_insurance_quote_enabled = fields.Boolean('Enable Insurance Quote', default=False)
