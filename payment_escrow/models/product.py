# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    broker_id = fields.Many2one('res.partner', string='Broker')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Escrow Car relations and attributes
    escrow_car_brand_id = fields.Many2one('escrow.car.brand', string='Car Brand')
    escrow_car_model_id = fields.Many2one('escrow.car.model', string='Car Model')
    escrow_car_model_year = fields.Char(string='Car Model Year')
    escrow_car_vin = fields.Char(string='Chassis (VIN)')
    escrow_car_plate = fields.Char(string='License Plate')
    escrow_owner_id = fields.Many2one('res.partner', string='Owner', domain=[('system', '=', 'escrow')])
    escrow_customer_id = fields.Many2one('res.partner', string='Customer', domain=[('paylox_escrow_type', '=', 'customer')])
    escrow_partner_id = fields.Many2one('res.partner', string='Partner', domain=[('system', '=', 'escrow')])
    escrow_payment_item_id = fields.Many2one('payment.item', string='Payment Items')

    # No numeric constraint needed since Year is a record now

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system = self.env.context.get('active_system') or self.env.context.get('system')
        if system == 'escrow':
            self = self.with_context(skip_view_mapping=True)
        return super(ProductProduct, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
