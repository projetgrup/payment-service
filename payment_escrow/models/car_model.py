# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EscrowCarModel(models.Model):
    _name = 'escrow.car.model'
    _description = 'Escrow Car Model'
    _order = 'brand_id, name'

    name = fields.Char(required=True, string='Model Name')
    brand_id = fields.Many2one('escrow.car.brand', string='Brand', ondelete='restrict', required=True)
    model_id = fields.Integer(string='Model ID')
    active = fields.Boolean(default=True, string='Active')