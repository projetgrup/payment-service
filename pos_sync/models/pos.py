# -*- coding: utf-8 -*-
from odoo import models, fields


class PosSync(models.Model):
    _name = 'pos.sync'
    _description = 'Point of Sale - Sync'

    name = fields.Char()
    data = fields.Text()
    cashier_id = fields.Integer()
    session_id = fields.Many2one('pos.session')
