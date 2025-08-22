# -*- coding: utf-8 -*-

from odoo import models, fields


class EscrowCarBrand(models.Model):
    _name = 'escrow.car.brand'
    _description = 'Escrow Car Brand'

    name = fields.Char(required=True, string='Brand')
