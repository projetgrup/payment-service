# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    broker_id = fields.Many2one('res.partner', string='Broker')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system = self.env.context.get('active_system') or self.env.context.get('system')
        if system == 'escrow':
            self = self.with_context(skip_view_mapping=True)
        return super(ProductTemplate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
