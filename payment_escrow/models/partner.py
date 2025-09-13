# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    paylox_escrow_type = fields.Selection([
        ('customer', 'Customer'),
        ('broker', 'Broker'),
        ('owner', 'Owner'),
        ('platform_owner', 'Platform Owner'),
        ('infrastructure_provider', 'Infrastructure Provider'),
        ('card_holder', 'Card Holder'),
    ], string='Paylox Escrow Type')

    installment_rate_ids = fields.One2many('escrow.installment.rate', 'partner_id', string='Installment Rates', domain=[('active', '=', True)])
    escrow_owner_ad_count = fields.Integer(string='Owner Ads Count', compute='_compute_escrow_counts')
    escrow_customer_ad_count = fields.Integer(string='Customer Ads Count', compute='_compute_escrow_counts')
    escrow_successful_payment_count = fields.Integer(string='Successful Payments Count', compute='_compute_escrow_counts')
    escrow_failed_payment_count = fields.Integer(string='Failed Payments Count', compute='_compute_escrow_counts')
    escrow_pending_ad_count = fields.Integer(string='Ads Pending Approval', compute='_compute_escrow_counts')
    is_escrow_customer = fields.Boolean(string='Is Escrow Customer')
    card_holder_ids = fields.One2many('res.partner', 'escrow_customer_id', string='Card Holders', domain=[('paylox_escrow_type', '=', 'card_holder')])
    escrow_customer_id = fields.Many2one('res.partner', string='Related Customer')
    is_otp_verified = fields.Boolean(string='Is OTP Verified')
    is_card_verified = fields.Boolean(string='Is Card Verified')

    @api.depends()
    def _compute_escrow_counts(self):
        for partner in self:
            partner.escrow_owner_ad_count = self.env['product.product'].search_count([
                ('escrow_owner_id', '=', partner.id),
                ('company_id', '=', partner.company_id.id or self.env.company.id)
            ])
            
            partner.escrow_customer_ad_count = self.env['product.product'].search_count([
                ('escrow_customer_ids', '=', partner.id),
                ('company_id', '=', partner.company_id.id or self.env.company.id)
            ])
            
            partner.escrow_successful_payment_count = self.env['payment.transaction'].search_count([
                ('partner_id', '=', partner.id),
                ('state', '=', 'done'),
                ('company_id', '=', partner.company_id.id or self.env.company.id)
            ])

            partner.escrow_failed_payment_count = self.env['payment.transaction'].search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['error', 'cancel']),
                ('company_id', '=', partner.company_id.id or self.env.company.id)
            ])

            partner.escrow_pending_ad_count = self.env['product.product'].search_count([
                ('company_id', '=', partner.company_id.id or self.env.company.id),
                ('system', '=', 'escrow'),
                ('escrow_state', '=', 'waiting'),
            ]) if partner.paylox_escrow_type == 'platform_owner' else 0

    def action_view_owner_ads(self):
        return {
            'name': _('My Ads'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,kanban,form',
            'views': [
                (self.env.ref('payment_escrow.tree_ad').id, 'tree'),
                (self.env.ref('payment_escrow.kanban_ad').id, 'kanban'),
                (self.env.ref('payment_escrow.form_ad').id, 'form'),
            ],
            'domain': [('escrow_owner_id', '=', self.id)],
            'context': {
                'default_escrow_owner_id': self.id,
                'create': False,
            }
        }

    def action_view_customer_ads(self):
        return {
            'name': _('Registered Ads'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,kanban,form',
            'views': [
                (self.env.ref('payment_escrow.tree_ad').id, 'tree'),
                (self.env.ref('payment_escrow.kanban_ad').id, 'kanban'),
                (self.env.ref('payment_escrow.form_ad').id, 'form'),
            ],
            'domain': [('escrow_customer_ids', '=', self.id)],
            'context': {
                'default_escrow_customer_ids': self.id,
                'create': False,
            }
        }

    def action_view_successful_payments(self):
        return {
            'name': _('Successful Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.transaction',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.id),
                ('state', '=', 'done')
            ],
            'context': {
                'default_partner_id': self.id,
                'create': False,
            }
        }

    def action_view_failed_payments(self):
        return {
            'name': _('Failed Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.transaction',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.id),
                ('state', 'in', ['error', 'cancel'])
            ],
            'context': {
                'default_partner_id': self.id,
                'create': False,
            }
        }

    def action_view_pending_approval_ads(self):
        self.ensure_one()
        return {
            'name': _('Ads Pending Approval'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,kanban,form',
            'views': [
                (self.env.ref('payment_escrow.tree_ad').id, 'tree'),
                (self.env.ref('payment_escrow.kanban_ad').id, 'kanban'),
                (self.env.ref('payment_escrow.form_ad').id, 'form'),
            ],
            'domain': [
                ('company_id', '=', self.company_id.id or self.env.company.id),
                ('system', '=', 'escrow'),
                ('escrow_state', '=', 'waiting'),
            ],
            'context': {
                'create': False,
            }
        }

    def action_payable(self):
        action = super(Partner, self).action_payable()
        system = self.company_id and self.company_id.system or self.env.context.get('active_system')
        if system == 'escrow':
            action['context']['domain'] = self.ids
        return action

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if view_type == 'form' and self.env.context.get('form_view_ref'):
            view_id = self.env.ref(self.env.context['form_view_ref']).id
        elif view_type == 'tree' and self.env.context.get('tree_view_ref'):
            view_id = self.env.ref(self.env.context['tree_view_ref']).id
        elif view_type == 'kanban' and self.env.context.get('kanban_view_ref'):
            view_id = self.env.ref(self.env.context['kanban_view_ref']).id
        elif view_type in ('form', 'tree', 'kanban'):
            system = self.env.context.get('active_system') or self.env.context.get('system')
            if system == 'escrow':
                type = self.env.context.get('active_escrow_type', 'owner')  # Varsayılan olarak 'owner' kullan
                try:
                    view_id = self.env.ref('payment_escrow.%s_%s' % (view_type, type)).id
                    self = self.with_context(skip_view_mapping=True)
                except:
                    # View bulunamazsa varsayılan owner view'ını dene
                    try:
                        view_id = self.env.ref('payment_escrow.%s_owner' % view_type).id
                        self = self.with_context(skip_view_mapping=True)
                    except:
                        # Hiçbiri bulunamazsa default view'ı kullan
                        pass
        return super(Partner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
