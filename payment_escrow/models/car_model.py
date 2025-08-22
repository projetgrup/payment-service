# -*- coding: utf-8 -*-

from odoo import models, fields


class EscrowCarModel(models.Model):
    _name = 'escrow.car.model'
    _description = 'Escrow Car Model'

    name = fields.Char(required=True, string='Model')
    brand_id = fields.Many2one('escrow.car.brand', string='Brand', ondelete='restrict')
