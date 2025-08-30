# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    broker_id = fields.Many2one('res.partner', string='Broker')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_escrow_customer_count(self):
        for product in self:
            product.escrow_customer_count = len(product.escrow_customer_ids)

    # Escrow Car relations and attributes
    escrow_car_brand_id = fields.Many2one('escrow.car.brand', string='Car Brand')
    escrow_car_model_id = fields.Many2one('escrow.car.model', string='Car Model')
    escrow_car_model_year = fields.Char(string='Car Model Year')
    escrow_car_vin = fields.Char(string='Chassis (VIN)')
    escrow_car_plate = fields.Char(string='License Plate')
    escrow_owner_id = fields.Many2one('res.partner', string='Owner', domain=[('system', '=', 'escrow')])
    escrow_customer_ids = fields.Many2many('res.partner', string='Customer', domain=[('paylox_escrow_type', '=', 'customer')])
    escrow_customer_count = fields.Integer(string='Customer Count', compute='_compute_escrow_customer_count')
    escrow_partner_id = fields.Many2one('res.partner', string='Partner', domain=[('system', '=', 'escrow')])
    escrow_payment_item_id = fields.Many2one('payment.item', string='Payment Items')
    escrow_payment_paid = fields.Boolean(string='Payment Item Paid', related='escrow_payment_item_id.paid', store=True, readonly=True)
    escrow_ad_sale_img = fields.Binary(string='Sale Image')
    escrow_ad_approval = fields.Boolean(string='Ad Approved')

    def action_get_customer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customers'),
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'domain': [('id', 'in', self.escrow_customer_ids.ids)],
            'context': dict(self.env.context),
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system = self.env.context.get('active_system') or self.env.context.get('system')
        if system == 'escrow':
            self = self.with_context(skip_view_mapping=True)
        return super(ProductProduct, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    def action_view_full_image(self):
        self.ensure_one()
        if not self.image_1920:
            raise UserError('Resim bulunamadı.')
        url = '/web/image/%s/%s/%s' % (self._name, self.id, 'image_1920')
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_approve_ad(self):
        for rec in self:
            user_partner = self.env.user.partner_id
            if user_partner.paylox_escrow_type != 'platform_owner':
                raise UserError(_('Only Platform Owner can approve ads.'))
            
            if not rec.escrow_payment_item_id or not rec.escrow_payment_item_id.paid:
                raise UserError(_('Payment item must be paid to approve this ad.'))
            
            if not rec.escrow_ad_sale_img:
                raise UserError(_('Sale image is required to approve this ad.'))
            rec.escrow_ad_approval = True
        return True



class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
