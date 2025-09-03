# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentEscrowAd(models.Model):
    _name = 'payment.escrow.ad'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = 'Payment Escrow Ads'

    def _compute_escrow_customer_count(self):
        for product in self:
            product.escrow_customer_count = len(product.escrow_customer_ids)

    name = fields.Char()
    ref = fields.Char()
    priority = fields.Integer('Priority', required=True)
    approved = fields.Boolean(string='Approved')
    owner_id = fields.Many2one('res.partner', string='Owner', domain=[('system', '=', 'escrow')])
    partner_id = fields.Many2one('res.partner', string='Partner', domain=[('system', '=', 'escrow')])
    product_id = fields.Many2one('product.product', string='Product', domain=[('system', '=', 'escrow')])
    customer_ids = fields.Many2many('res.partner', string='Customer', domain=[('paylox_escrow_type', '=', 'customer')])
    customer_count = fields.Integer(string='Customer Count', compute='_compute_escrow_customer_count')
    item_ids = fields.One2many('payment.item', 'system_escrow_ad_id', copy=False)
    currency_id = fields.Many2one('res.currency', readonly=True)

    category_car_vin = fields.Char(string='Chassis (VIN)')
    category_car_plate = fields.Char(string='License Plate')
