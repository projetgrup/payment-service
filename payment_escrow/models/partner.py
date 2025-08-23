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
    ], string='Paylox Escrow Type')

    # Smart Button Computed Fields
    escrow_owner_ad_count = fields.Integer(
        string='Owner Ads Count',
        compute='_compute_escrow_counts'
    )
    escrow_customer_ad_count = fields.Integer(
        string='Customer Ads Count',
        compute='_compute_escrow_counts'
    )
    escrow_successful_payment_count = fields.Integer(
        string='Successful Payments Count',
        compute='_compute_escrow_counts'
    )
    escrow_failed_payment_count = fields.Integer(
        string='Failed Payments Count',
        compute='_compute_escrow_counts'
    )

    @api.depends()
    def _compute_escrow_counts(self):
        for partner in self:
            # Owner'ın ilanları (product.product'daki escrow_owner_id field'ından)
            partner.escrow_owner_ad_count = self.env['product.product'].search_count([
                ('escrow_owner_id', '=', partner.id),
                ('company_id', '=', partner.company_id.id or self.env.company.id)
            ])
            
            # Customer'ın kayıt olduğu ilanlar (product.product'daki escrow_customer_id field'ından)
            partner.escrow_customer_ad_count = self.env['product.product'].search_count([
                ('escrow_customer_id', '=', partner.id),
                ('company_id', '=', partner.company_id.id or self.env.company.id)
            ])
            
            # Başarılı ödemeler (payment.transaction'dan)
            partner.escrow_successful_payment_count = self.env['payment.transaction'].search_count([
                ('partner_id', '=', partner.id),
                ('state', '=', 'done'),
                ('company_id', '=', partner.company_id.id or self.env.company.id)
            ])
            
            # Başarısız ödemeler
            partner.escrow_failed_payment_count = self.env['payment.transaction'].search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['error', 'cancel']),
                ('company_id', '=', partner.company_id.id or self.env.company.id)
            ])

    def action_view_owner_ads(self):
        """Owner'ın sahip olduğu ilanları göster"""
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
        """Customer'ın kayıt olduğu ilanları göster"""
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
            'domain': [('escrow_customer_id', '=', self.id)],
            'context': {
                'default_escrow_customer_id': self.id,
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
                type = self.env.context.get('active_escrow_type', '')
                try:
                    view_id = self.env.ref('payment_escrow.%s_%s' % (view_type, type)).id
                except:
                    raise UserError(_('View cannot be found'))
                self = self.with_context(skip_view_mapping=True)
        return super(Partner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
