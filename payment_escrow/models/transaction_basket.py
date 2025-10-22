# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PaymentTransactionBasket(models.Model):
    _inherit = 'payment.transaction.basket'

    product_id = fields.Many2one('product.product', string='Product (Ad)', compute='_compute_escrow_fields', store=True)
    ad_number = fields.Char(string='Ad Number', compute='_compute_escrow_fields', store=True)
    vehicle_info = fields.Char(string='Vehicle Info', compute='_compute_escrow_fields', store=True)
    
    acquirer_id = fields.Many2one('payment.acquirer', string='Payment Provider', related='transaction_id.acquirer_id', store=True, readonly=True)
    vpos_name = fields.Char(string='Virtual POS Name', related='transaction_id.jetcheckout_vpos_name', store=True, readonly=True)
    transaction_date = fields.Datetime(string='Transaction Date', related='transaction_id.create_date', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='transaction_id.currency_id', store=True, readonly=True)
    
    ad_state = fields.Selection([
        ('waiting', 'Waiting'),
        ('new', 'New'),
        ('waiting_official_sale_img', 'Waiting Official Sale Image'),
        ('waiting_transfer_approval', 'Waiting Transfer Approval'),
        ('transferred', 'Transferred'),
    ], string='Ad Status', compute='_compute_escrow_fields', store=True)
    
    transfer_account = fields.Char(string='Transfer Account', compute='_compute_transfer_account', store=True)
    api_charged_amount = fields.Monetary(string='API Charged Amount', related='transaction_id.jetcheckout_payment_paid', store=True, readonly=True)
    transfer_amount = fields.Monetary(string='Transfer Amount', help='Amount to be transferred')
    paylox_escrow_type = fields.Selection([
        ('platform_owner', 'Platform Owner'),
        ('infrastructure_provider', 'Infrastructure Provider'),
        ('broker', 'Broker'),
        ('owner', 'Owner'),
        ('customer', 'Customer'),
        ('card_holder', 'Card Holder'),
    ], string='Paylox Escrow Type', compute='_compute_escrow_fields', store=True)

    transfer_status = fields.Selection([
        ('can_approve', 'Transfer Can Be Approved'),
        ('waiting_invoice', 'Waiting for Invoice'),
        ('approved', 'Transfer Approved'),
    ], string='Transfer Status', compute='_compute_transfer_status', store=True)
    
    broker_invoice_id = fields.Many2one('ir.attachment', string='Broker Invoice')
    broker_invoice_filename = fields.Char(string='Invoice Filename', compute='_compute_broker_invoice_filename', store=True)
    broker_invoice_upload_date = fields.Datetime(string='Invoice Upload Date')
    broker_submitted_for_approval = fields.Boolean(string='Submitted for Approval', default=False)
    broker_submit_date = fields.Datetime(string='Submit Date')

    escrow_success_group = fields.Selection(
        selection=[('successful', 'Successful'), ('unsuccessful', 'Unsuccessful')],
        string='Escrow Success Group',
        related='transaction_id.escrow_success_group',
        store=True,
        index=True,
        readonly=True,
    )

    @api.depends('broker_invoice_id', 'broker_invoice_id.name')
    def _compute_broker_invoice_filename(self):
        for record in self:
            record.broker_invoice_filename = record.broker_invoice_id.name if record.broker_invoice_id else False

    @api.depends('transaction_id', 'transaction_id.jetcheckout_item_ids', 'transaction_id.paylox_product_ids', 'submerchant_external_id')
    def _compute_escrow_fields(self):
        for basket in self:
            product = False
            ad_number = ''
            vehicle_info = ''
            ad_state = False
            
            if basket.submerchant_external_id:
                partner_bank = self.env['res.partner.bank'].sudo().search([
                    ('api_ref', '=', basket.submerchant_external_id)
                ], limit=1)
                if partner_bank and partner_bank.partner_id:
                    escrow_type = partner_bank.partner_id.paylox_escrow_type
                    if escrow_type and escrow_type != 'customer':
                        basket.paylox_escrow_type = escrow_type

            if basket.transaction_id:
                if basket.transaction_id.jetcheckout_item_ids:
                    item = basket.transaction_id.jetcheckout_item_ids[0]
                    if item.product_id:
                        product = item.product_id
                
                elif basket.transaction_id.paylox_product_ids:
                    product_line = basket.transaction_id.paylox_product_ids[0]
                    if product_line.product_id:
                        product = product_line.product_id

            if product:
                ad_number = product.default_code or str(product.id)
                ad_state = product.escrow_state
                
                parts = []
                if product.escrow_car_brand_id:
                    parts.append(product.escrow_car_brand_id.name)
                if product.escrow_car_model_id:
                    parts.append(product.escrow_car_model_id.name)
                if product.escrow_car_model_year:
                    parts.append(str(product.escrow_car_model_year))
                if product.escrow_car_plate:
                    parts.append(product.escrow_car_plate)
                vehicle_info = ' / '.join(parts) if parts else product.name
            
            basket.product_id = product.id if product else False
            basket.ad_number = ad_number
            basket.vehicle_info = vehicle_info
            basket.ad_state = ad_state
            basket.transfer_amount = basket.submerchant_price or 0.0

    @api.depends('approval_state', 'ad_state', 'paylox_escrow_type', 'broker_invoice_id', 'transaction_id.jetcheckout_approval_state')
    def _compute_transfer_status(self):
        for basket in self:
            transfer_status = False
            
            if basket.approval_state == '+':
                transfer_status = 'approved'
            elif basket.approval_state == '-':
                if basket.paylox_escrow_type == 'broker':
                    if basket.ad_state == 'waiting_official_sale_img':
                        transfer_status = 'waiting_invoice'
                    elif basket.ad_state in ['waiting_transfer_approval', 'transferred']:
                        transfer_status = 'can_approve'
                    else:
                        transfer_status = 'waiting_invoice'
                else:
                    transfer_status = 'can_approve'
            else:
                if basket.paylox_escrow_type == 'broker':
                    if basket.broker_invoice_id:
                        transfer_status = 'can_approve'
                    else:
                        transfer_status = 'waiting_invoice'
                else:
                    transfer_status = 'can_approve'

            basket.transfer_status = transfer_status

    @api.depends('submerchant_external_id')
    def _compute_transfer_account(self):
        for basket in self:
            transfer_account = ''
            if basket.submerchant_external_id:
                partner = self.env['res.partner.bank'].sudo().search([
                    ('api_ref', '=', basket.submerchant_external_id)
                ], limit=1)
                if partner:
                    transfer_account = partner.acc_number or ''
            basket.transfer_account = transfer_account

    def action_recompute_fields(self):
        for basket in self:
            basket._compute_escrow_fields()
            basket._compute_transfer_status()
            basket._compute_transfer_account()
        return True

    def action_approve_payment(self):
        for basket in self:
            basket._action_approve_payment()
    
    def _action_approve_payment(self):
        if self.transfer_status != 'can_approve':
            self.write({'approval_state_message': _('This payment basket is not eligible for approval.')})
            raise UserError(_('This payment basket is not eligible for approval.'))
        self.action_approve()

    def write(self, values):
        res = super().write(values)
        if values.get('broker_submitted_for_approval'):
            group = self.env.ref('payment_escrow.group_escrow_manager')
            for basket in self:
                users = self.env['res.users'].search([
                    ('company_id', '=', basket.transaction_id.company_id.id),
                    ('groups_id', 'in', group.ids)
                ])
                template = self.env.ref('payment_escrow.email_template_platform_owner_payment_waiting_approval')
                url = '%s/web#id=%s&model=%s&view_type=form' % (self.get_base_url(), basket.id, basket._name)
                for user in users:
                    user.partner_id.with_context(url=url, skip_queue=True).message_post_with_template(
                        template.id, composition_mode='comment',
                        email_layout_xmlid='mail.mail_notification_light',
                    )
        return res
