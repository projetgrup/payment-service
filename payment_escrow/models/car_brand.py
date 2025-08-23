# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EscrowCarBrand(models.Model):
    _name = 'escrow.car.brand'
    _description = 'Escrow Car Brand'
    _order = 'name'

    name = fields.Char(required=True, string='Brand Name')
    active = fields.Boolean(default=True, string='Active')
    logo = fields.Binary(string='Brand Logo')
    model_ids = fields.One2many('escrow.car.model', 'brand_id', string='Models')