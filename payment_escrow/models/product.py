# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    broker_id = fields.Many2one('res.partner', string='Broker')


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'mail.thread', 'mail.activity.mixin']


    def _compute_escrow_customer_count(self):
        for product in self:
            product.escrow_customer_count = len(product.escrow_customer_ids)

    def _compute_is_platform_owner_user(self):
        is_platform_owner = self.env.user.partner_id.paylox_escrow_type == 'platform_owner'
        for rec in self:
            rec.is_platform_owner_user = is_platform_owner

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
    escrow_ad_official_sale_img = fields.Binary(string='Official Sale Image')
    is_platform_owner_user = fields.Boolean(string='Is Platform Owner User', compute='_compute_is_platform_owner_user', store=False)
    escrow_unapproved_transfer_count = fields.Integer(string='Unapproved Transfers', compute='_compute_escrow_transfer_count')
    escrow_approved_transfer_count = fields.Integer(string='Approved Transfers', compute='_compute_escrow_transfer_count')
    escrow_transfer_count_display = fields.Char(string='Transfers', compute='_compute_escrow_transfer_count')
    sale_state = fields.Selection([
        ('waiting_payment', 'Waiting Payment'),
        ('waiting_official_doc', 'Waiting Official Document'),
        ('waiting_transfer', 'Waiting Transfer Approval'),
        ('transferred', 'Transferred'),
        ('sold', 'Sold'),
    ], string='State', default='waiting_payment', index=True, tracking=True, copy=False)
    escrow_license_serial_no = fields.Char(string='License Serial No')

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

    def _compute_escrow_transfer_count(self):
        for rec in self:
            unapproved = 0
            approved = 0
            if rec.escrow_payment_item_id:
                items = rec.escrow_payment_item_id.mapped('transaction_ids.paylox_basket_ids').filtered(
                    lambda b: b.transaction_id.state == 'done'
                )
                for item in items:
                    if item.approval_state == '+':
                        approved += 1
                    else:
                        unapproved += 1
            rec.escrow_unapproved_transfer_count = unapproved
            rec.escrow_approved_transfer_count = approved
            rec.escrow_transfer_count_display = f"{unapproved}/{approved}"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system = self.env.context.get('active_system') or self.env.context.get('system')
        if system == 'escrow':
            self = self.with_context(skip_view_mapping=True)
        return super(ProductProduct, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    def action_approve_ad(self):
        for rec in self:
            user_partner = self.env.user.partner_id
            if user_partner.paylox_escrow_type != 'platform_owner':
                raise UserError(_('Only Platform Owner can approve ads.'))
            
            if not rec.escrow_ad_sale_img:
                raise UserError(_('Sale image is required to approve this ad.'))
            rec.sale_state = 'waiting_payment'
        return True

    def action_view_basket_items(self):
        self.ensure_one()
        action = self.env.ref('payment_escrow.action_payment_transaction_basket').sudo().read()[0]
        txs = self.escrow_payment_item_id.transaction_ids
        action['domain'] = [
            ('transaction_id', 'in', txs.ids),
            ('transaction_id.state', 'in', ['done'])
        ]
        action['context'] = {
            'create': False,
            'edit': False,
            'delete': False,
            'group_by': 'escrow_success_group',
        }
        return action

class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
