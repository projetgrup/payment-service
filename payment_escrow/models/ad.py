# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EscrowAd(models.Model):
    _name = 'escrow.ad'
    _description = 'Escrow Advertisement'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'create_date desc, id desc'

    active = fields.Boolean(default=True, tracking=True)
    name = fields.Char(compute='_compute_name', store=True, readonly=False, required=True, tracking=True, index=True)
    description = fields.Html(tracking=True)
    reference = fields.Char(string='Ad Reference', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    
    category_id = fields.Many2one('escrow.ad.category', required=True, tracking=True, ondelete='restrict', index=True)
    category_type = fields.Selection(related='category_id.category_type', store=True, readonly=True)
    
    broker_id = fields.Many2one('res.partner', tracking=True, domain=[('system', '=', 'escrow')], index=True)
    owner_id = fields.Many2one('res.partner', tracking=True, domain=[('system', '=', 'escrow')], index=True)
    customer_ids = fields.Many2many('res.partner', 'escrow_ad_customer_rel', 'ad_id', 'partner_id', string='Registered Customers', domain=[('paylox_escrow_type', '=', 'customer')])
    customer_count = fields.Integer(compute='_compute_customer_count', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('new', 'Published'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True, index=True, copy=False)
    
    sale_state = fields.Selection([
        ('waiting_payment', 'Waiting Payment'),
        ('waiting_official_doc', 'Waiting Official Document'),
        ('waiting_transfer', 'Waiting Transfer Approval'),
        ('transferred', 'Transferred'),
    ], tracking=True, index=True, copy=False)
    
    price = fields.Monetary(required=True, tracking=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    
    
    image_ids = fields.One2many('escrow.ad.image', 'ad_id', string='Images')
    image_count = fields.Integer(compute='_compute_image_count', store=True)
    
    payment_item_id = fields.Many2one('payment.item', string='Payment Item', copy=False, readonly=True)
    payment_paid = fields.Boolean(related='payment_item_id.paid', store=True, readonly=True)
    
    official_sale_document = fields.Binary(attachment=True)
    official_sale_document_name = fields.Char()
    official_sale_upload_date = fields.Datetime(readonly=True)
    
    attribute_value_ids = fields.One2many('escrow.ad.attribute.value', 'ad_id', string='Attribute Values')
    
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, index=True)
    
    view_count = fields.Integer(default=0, readonly=True)
    favorite_count = fields.Integer(compute='_compute_favorite_count', store=True)
    
    is_featured = fields.Boolean(default=False, tracking=True)
    featured_until = fields.Datetime(tracking=True)
    
    unapproved_transfer_count = fields.Integer(compute='_compute_transfer_count', store=True)
    approved_transfer_count = fields.Integer(compute='_compute_transfer_count', store=True)
    transfer_count_display = fields.Char(compute='_compute_transfer_count')
    
    @api.depends('customer_ids')
    def _compute_customer_count(self):
        for ad in self:
            ad.customer_count = len(ad.customer_ids)
    
    @api.depends('image_ids')
    def _compute_image_count(self):
        for ad in self:
            ad.image_count = len(ad.image_ids)
    
    @api.depends('payment_item_id', 'payment_item_id.transaction_ids')
    def _compute_transfer_count(self):
        for ad in self:
            unapproved = 0
            approved = 0
            if ad.payment_item_id:
                items = ad.payment_item_id.mapped('transaction_ids.paylox_basket_ids').filtered(
                    lambda b: b.transaction_id.state == 'done'
                )
                for item in items:
                    if item.approval_state == '+':
                        approved += 1
                    else:
                        unapproved += 1
            ad.unapproved_transfer_count = unapproved
            ad.approved_transfer_count = approved
            ad.transfer_count_display = f"{unapproved}/{approved}"
    
    def _compute_favorite_count(self):
        for ad in self:
            ad.favorite_count = self.env['escrow.ad.favorite'].search_count([('ad_id', '=', ad.id)])
    
    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('escrow.ad') or _('New')
        return super().create(vals)
    
    def action_submit_for_approval(self):
        self.write({'state': 'waiting'})
        self._notify_platform_owners()
        return True
    
    def action_approve(self):
        user_partner = self.env.user.partner_id
        if user_partner.paylox_escrow_type != 'platform_owner':
            raise UserError(_('Only Platform Owner can approve ads.'))
        self.write({'state': 'new'})
        return True
    
    def action_reject(self):
        user_partner = self.env.user.partner_id
        if user_partner.paylox_escrow_type != 'platform_owner':
            raise UserError(_('Only Platform Owner can reject ads.'))
        self.write({'state': 'cancelled'})
        return True
    
    def action_set_sold(self):
        self.write({'state': 'sold'})
        return True
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True
    
    def action_view_customers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Registered Customers'),
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'domain': [('id', 'in', self.customer_ids.ids)],
            'context': {'create': False},
        }
    
    def action_view_images(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ad Images'),
            'view_mode': 'kanban,tree,form',
            'res_model': 'escrow.ad.image',
            'domain': [('ad_id', '=', self.id)],
            'context': {'default_ad_id': self.id},
        }
    
    def action_view_basket_items(self):
        self.ensure_one()
        action = self.env.ref('payment_escrow.action_payment_transaction_basket').sudo().read()[0]
        txs = self.payment_item_id.transaction_ids
        action['domain'] = [
            ('transaction_id', 'in', txs.ids),
            ('transaction_id.state', 'in', ['done', 'error', 'cancel', 'expired'])
        ]
        action['context'] = {
            'create': False,
            'edit': False,
            'delete': False,
            'group_by': 'escrow_success_group',
        }
        return action
    
    def _notify_platform_owners(self):
        platform_group = self.env.ref('payment_escrow.group_escrow_platform_owner')
        platform_owners = self.env['res.partner'].search([
            ('user_ids.groups_id', 'in', platform_group.id),
            ('company_id', '=', self.company_id.id),
        ])
        for owner in platform_owners:
            if owner.user_ids:
                self.env['mail.activity'].create({
                    'res_id': self.id,
                    'res_model_id': self.env.ref('payment_escrow.model_escrow_ad').id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': _('New Ad Pending Approval'),
                    'note': _('Ad "%s" has been submitted and is pending approval.') % self.name,
                    'user_id': owner.user_ids[0].id,
                })

    @api.depends('attribute_value_ids.display_value', 'attribute_value_ids.attribute_id.is_name_part', 
                 'attribute_value_ids.attribute_id.name_sequence', 'attribute_value_ids.attribute_id.technical_name')
    def _compute_name(self):
        for ad in self:
            title_attr = ad.attribute_value_ids.filtered(lambda v: v.attribute_id.technical_name in ['title', 'name'])
            if title_attr and title_attr[0].display_value:
                ad.name = title_attr[0].display_value
            else:
                parts = ad.attribute_value_ids.filtered(lambda v: v.attribute_id.is_name_part).sorted(key=lambda v: v.attribute_id.name_sequence)
                if parts:
                    valid_parts = parts.filtered(lambda p: p.display_value)
                    if valid_parts:
                        ad.name = ' | '.join(valid_parts.mapped('display_value'))
                    elif not ad.name:
                         ad.name = _('New Advertisement')
                elif not ad.name:
                    ad.name = _('New Advertisement')

    def get_attribute_value(self, technical_name):
        self.ensure_one()
        attr_value = self.attribute_value_ids.filtered(lambda v: v.attribute_id.technical_name == technical_name)
        return attr_value and attr_value[0].display_value or ''

class EscrowBrandSyncJob(models.Model):
    _name = 'escrow.brand.sync.job'

class EscrowAdImage(models.Model):
    _name = 'escrow.ad.image'
    _description = 'Advertisement Image'
    _order = 'sequence, id'

    ad_id = fields.Many2one('escrow.ad', required=True, ondelete='cascade', index=True)
    image = fields.Binary(required=True, attachment=True)
    image_filename = fields.Char()
    sequence = fields.Integer(default=10)
    is_main = fields.Boolean(default=False)
    
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.is_main:
            self.search([
                ('ad_id', '=', res.ad_id.id),
                ('id', '!=', res.id),
                ('is_main', '=', True)
            ]).write({'is_main': False})
        return res
    
    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_main'):
            for rec in self:
                self.search([
                    ('ad_id', '=', rec.ad_id.id),
                    ('id', '!=', rec.id),
                    ('is_main', '=', True)
                ]).write({'is_main': False})
        return res


class EscrowAdFavorite(models.Model):
    _name = 'escrow.ad.favorite'
    _description = 'Favorite Advertisement'
    _rec_name = 'ad_id'

    ad_id = fields.Many2one('escrow.ad', required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade', index=True)
    
    _sql_constraints = [
        ('unique_ad_partner', 'unique(ad_id, partner_id)', 'This ad is already in favorites!')
    ]

class PaymentTransactionProduct(models.Model):
    _inherit = 'payment.transaction.product'

    ad_id = fields.Many2one('escrow.ad')