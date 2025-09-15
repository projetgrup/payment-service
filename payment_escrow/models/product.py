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
            rec.is_platform_owner_user = True

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
    escrow_state = fields.Selection([
        ('waiting', 'Waiting'),
        ('new', 'New'),
        ('waiting_official_sale_img', 'Waiting Official Sale Image'),
        ('transferred', 'Transferred'),
    ], string='State', default='waiting', index=True, tracking=True)

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
                domain = [
                    ('state', '=', 'done'),
                    ('acquirer_id.provider', '=', 'jetcheckout'),
                    ('jetcheckout_payment_type', '=', 'virtual_pos'),
                    ('jetcheckout_approval_state', '!=', '+'),
                    ('jetcheckout_item_ids', 'in', rec.escrow_payment_item_id.ids),
                ]
                unapproved = self.env['payment.transaction'].sudo().search_count(domain)
                domain[3] = ('jetcheckout_approval_state', '=', '+')
                approved = self.env['payment.transaction'].sudo().search_count(domain)
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
            
            if not rec.escrow_payment_item_id or not rec.escrow_payment_item_id.paid:
                raise UserError(_('Payment item must be paid to approve this ad.'))
            
            if not rec.escrow_ad_sale_img:
                raise UserError(_('Sale image is required to approve this ad.'))
            rec.escrow_state = 'new'
        return True

    def action_view_transactions(self):
        self.ensure_one()
        user_partner = self.env.user.partner_id
        # if user_partner.paylox_escrow_type != 'platform_owner':
        #     raise UserError(_('Only Platform Owner can view transactions.'))

        action = self.env.ref('payment_jetcheckout_system.action_transaction').sudo().read()[0]
        domain = [('state', 'in', ['done', 'error', 'cancel', 'expired'])]
        if self.escrow_payment_item_id:
            domain.append(('jetcheckout_item_ids', 'in', self.escrow_payment_item_id.ids))
        else:
            domain.append(('id', '=', 0))
        action['domain'] = domain
        action['context'] = {
            'create': False,
            'edit': False,
            'delete': False,
            'group_by': 'escrow_success_group',
        }
        return action

    def action_approve_transfers(self):
        self.ensure_one()
        # if self.env.user.partner_id.paylox_escrow_type != 'platform_owner':
        #     raise UserError(_('Only Platform Owner can approve transfers.'))

        if not self.escrow_payment_item_id:
            raise UserError(_('There is no related payment item for this ad.'))

        domain = [
            ('state', '=', 'done'),
            ('acquirer_id.provider', '=', 'jetcheckout'),
            ('jetcheckout_payment_type', '=', 'virtual_pos'),
            ('jetcheckout_approval_state', '!=', '+'),
            ('jetcheckout_item_ids', 'in', self.escrow_payment_item_id.ids),
        ]
        txs = self.env['payment.transaction'].sudo().search(domain)
        if not txs:
            raise UserError(_('No unapproved transfer transactions found.'))
        success_count = 0
        failures = []
        for tx in txs:
            try:
                tx.action_approve()
                if tx.jetcheckout_approval_state == '+':
                    success_count += 1
                else:
                    failures.append('%s: %s' % (
                        tx.reference or str(tx.id),
                        tx.jetcheckout_approval_state_message or '-' 
                    ))
            except Exception as e:
                failures.append('%s: %s' % (tx.reference or str(tx.id), str(e)))

        total = len(txs)
        fail_count = len(failures)

        title = _('Transfer Approval Result')
        summary = _('Approved %(ok)s of %(total)s transfer transactions. Failures: %(fail)s.') % {
            'ok': success_count,
            'total': total,
            'fail': fail_count,
        }
        body = '<p><b>%s</b></p><p>%s</p>' % (title, summary)
        if fail_count:
            body += '<ul>' + ''.join(['<li>%s: %s</li>' % (ref, msg) for ref, msg in [
                (line.split(':', 1)[0], line.split(':', 1)[1].strip() if ':' in line else '') for line in failures
            ]]) + '</ul>'
        else:
            self.escrow_state = 'transferred'
        self.message_post(body=body, subtype_xmlid='mail.mt_note')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': _('Details have been posted to chatter.'),
                'type': 'success' if fail_count == 0 else 'warning',
                'sticky': fail_count > 0,
            }
        }

class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
