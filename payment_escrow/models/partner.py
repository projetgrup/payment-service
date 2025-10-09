# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('default_system') == 'escrow' and 'user_id' in fields and not res.get('user_id'):
            res['user_id'] = self.env.user.id
        return res

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
    
    broker_campaign_id = fields.Many2many('escrow.broker.campaign', string='Broker Campaign')
    broker_default_campaign_id = fields.Many2one('escrow.broker.campaign', string='Default Campaign')
    broker_sign_name = fields.Char(string='Sign Name')
    broker_authorized_person = fields.Char(string='Authorized Person')
    broker_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Broker Status', default='draft')
    broker_tax_plate = fields.Binary(string='Tax Plate', attachment=True)
    broker_tax_plate_filename = fields.Char(string='Tax Plate Filename')
    broker_signature_circular = fields.Binary(string='Signature Circular', attachment=True)
    broker_signature_circular_filename = fields.Char(string='Signature Circular Filename')
    broker_identity_doc = fields.Binary(string='Identity Document', attachment=True)
    broker_identity_doc_filename = fields.Char(string='Identity Document Filename')
    broker_authorization_doc = fields.Binary(string='Authorization Document', attachment=True)
    broker_authorization_doc_filename = fields.Char(string='Authorization Document Filename')
    broker_contract = fields.Binary(string='Contract', attachment=True)
    broker_contract_filename = fields.Char(string='Contract Filename')
    broker_approval_date = fields.Datetime(string='Approval Date', readonly=True)
    broker_approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    broker_rejection_reason = fields.Text(string='Rejection Reason')

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

    def _is_platform_owner(self):
        current_partner = self.env.user.partner_id
        return current_partner.paylox_escrow_type == 'platform_owner'

    def action_approve_broker(self):
        self.ensure_one()
        
        if not self._is_platform_owner():
            raise UserError(_('Only platform owners can approve brokers.'))
        
        if self.paylox_escrow_type != 'broker':
            raise UserError(_('This action is only available for brokers.'))
        
        self.write({
            'broker_state': 'approved',
            'broker_approval_date': fields.Datetime.now(),
            'broker_approved_by': self.env.user.id,
        })
        
        self._create_broker_portal_user()
        self._send_broker_approval_notification()
        
        return True
    
    def _create_broker_portal_user(self):
        self.ensure_one()
        if self.user_ids:
            portal_group = self.env.ref('base.group_portal')
            for user in self.user_ids:
                if portal_group not in user.groups_id:
                    user.write({'groups_id': [(4, portal_group.id)]})
            return
        
        if not self.email:
            raise UserError(_('Cannot create portal user: Broker email is required.'))
        
        existing_user = self.env['res.users'].search([('login', '=', self.email)], limit=1)
        if existing_user:
            raise UserError(_('A user with email "%s" already exists.') % self.email)
        
        portal_group = self.env.ref('base.group_portal')
        
        user_vals = {
            'name': self.name,
            'login': self.email,
            'email': self.email,
            'partner_id': self.id,
            'groups_id': [(6, 0, [portal_group.id])],
            'company_id': self.company_id.id or self.env.company.id,
            'company_ids': [(6, 0, [self.company_id.id or self.env.company.id])],
        }
        
        try:
            user = self.env['res.users'].sudo().create(user_vals)
            user.sudo().with_context(create_user=True).action_reset_password()
            
        except Exception as e:
            raise UserError(_('Error creating portal user: %s') % str(e))
    
    def action_reject_broker(self):
        self.ensure_one()
        
        if not self._is_platform_owner():
            raise UserError(_('Only platform owners can reject brokers.'))
        
        if self.paylox_escrow_type != 'broker':
            raise UserError(_('This action is only available for brokers.'))
        
        return {
            'name': _('Reject Broker'),
            'type': 'ir.actions.act_window',
            'res_model': 'broker.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_broker_id': self.id},
        }
    
    def action_set_to_pending(self):
        self.ensure_one()
        if self.paylox_escrow_type != 'broker':
            raise UserError(_('This action is only available for brokers.'))
        self.write({'broker_state': 'pending'})
        self._notify_platform_owners_new_broker()
        
        return True
    
    def _send_broker_approval_notification(self):
        if self.email:
            template = self.env.ref('payment_escrow.email_template_broker_approved', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
    
    def _send_broker_rejection_notification(self):
        if self.email:
            template = self.env.ref('payment_escrow.email_template_broker_rejected', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
    
    def _notify_platform_owners_new_broker(self):
        platform_owners = self.env['res.partner'].search([
            ('paylox_escrow_type', '=', 'platform_owner'),
            ('company_id', '=', self.company_id.id),
        ])
        
        for owner in platform_owners:
            if owner.user_ids:
                self.env['mail.activity'].create({
                    'res_id': self.id,
                    'res_model_id': self.env.ref('base.model_res_partner').id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': _('New Broker Registration'),
                    'note': _('A new broker "%s" has registered and is pending approval.') % self.name,
                    'user_id': owner.user_ids[0].id,
                })
        
        template = self.env.ref('payment_escrow.email_template_broker_new_registration', raise_if_not_found=False)
        if template and platform_owners:
            for owner in platform_owners:
                if owner.email:
                    template.send_mail(self.id, force_send=True, email_values={'email_to': owner.email})

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
                type = self.env.context.get('active_escrow_type', 'owner')
                try:
                    view_id = self.env.ref('payment_escrow.%s_%s' % (view_type, type)).id
                    self = self.with_context(skip_view_mapping=True)
                except:
                    try:
                        view_id = self.env.ref('payment_escrow.%s_owner' % view_type).id
                        self = self.with_context(skip_view_mapping=True)
                    except:
                        pass
        return super(Partner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
