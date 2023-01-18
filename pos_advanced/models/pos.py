# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields


class PosBank(models.Model):
    _name = 'pos.bank'
    _description = 'Point of Sale - Bank'
    _order = 'sequence'

    config_id = fields.Many2one('pos.config')
    sequence = fields.Integer(default=10)
    logo = fields.Image()
    name = fields.Char(required=True)
    iban = fields.Char(string='IBAN')
    account = fields.Char(string='Account Number')
    branch = fields.Char()
    token = fields.Char(default=lambda self: str(uuid.uuid4()), readonly=True)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    cash_payment_limit_ok = fields.Boolean(string='Limit Cash Payment Amount')
    cash_payment_limit_amount = fields.Monetary(string='Cash Payment Amount Limit')
    bank_ids = fields.One2many('pos.bank', 'config_id', string='Banks')
    bank_ok = fields.Boolean(string='Show Bank Accounts')
