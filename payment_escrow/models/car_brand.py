# -*- coding: utf-8 -*-

from odoo import models, fields


class EscrowCarBrand(models.Model):
    _name = 'escrow.car.brand'
    _description = 'Escrow Car Brand'
    _order = 'name'

    name = fields.Char(required=True, string='Brand Name')
    brand_id = fields.Integer(string='Brand ID')
    active = fields.Boolean(default=True, string='Active')
    logo = fields.Binary(string='Brand Logo')
    model_ids = fields.One2many('escrow.car.model', 'brand_id', string='Models')


    def action_get_models(self):
        self.ensure_one()
        company = self.env.company
        result, message = self.env['syncops.connector'].sudo()._execute('other_get_vpic_model', reference=str(self.id), params={
            'brand': self.name
        },company=company,  message=True)
        if not result:
            raise Exception(message)
        for model in result:
            existing_model = self.model_ids.search([
                ('model_id', '=', model.get('model_id')),
                ('brand_id', '=', self.id)
            ], limit=1)
            if not existing_model:
                model_vals = {
                    'name': model.get('model'),
                    'model_id': model.get('model_id'),
                    'brand_id': self.id,
                    'active': True,
                }
                self.model_ids.create(model_vals)
