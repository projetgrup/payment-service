# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError
from odoo.osv import expression

from .approval_chain import ESCROW_DEFAULT_VISIBLE_TYPES


_logger = logging.getLogger(__name__)


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
        ('dealer', 'Dealer'),
        ('card_holder', 'Card Holder'),
    ], string='Paylox Escrow Type', compute='_compute_escrow_fields', store=True)

    transfer_status = fields.Selection([
        ('can_approve', 'Transfer Can Be Approved'),
        ('waiting_invoice', 'Waiting for Invoice'),
        ('approved', 'Transfer Approved'),
    ], string='Transfer Status', compute='_compute_transfer_status', store=True)
    
    broker_invoice_id = fields.Many2one('ir.attachment', string='Broker Invoice')
    broker_invoice_upload_id = fields.Binary(string='Upload Broker Invoice', related='broker_invoice_id.datas', readonly=True)
    broker_invoice_filename = fields.Char(string='Invoice Filename', compute='_compute_broker_invoice_filename', store=True)
    broker_invoice_upload_date = fields.Datetime(string='Invoice Upload Date')
    broker_submitted_for_approval = fields.Boolean(string='Submitted for Approval', default=False)
    broker_submit_date = fields.Datetime(string='Submit Date')
    partner_id = fields.Many2one('res.partner', string='Submerchant', readonly=True)

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

    @api.depends('transaction_id', 'transaction_id.jetcheckout_item_ids', 'transaction_id.paylox_product_ids', 'submerchant_external_id', 'partner_id')
    def _compute_escrow_fields(self):
        for basket in self:
            product = False
            ad_number = ''
            vehicle_info = ''
            ad_state = False
            approval_state = basket.transaction_id.jetcheckout_approval_state if basket.transaction_id else False
            escrow_type = False
            
            if basket.submerchant_external_id:
                partner_bank = self.env['res.partner.bank'].sudo().search([
                    ('api_ref', '=', basket.submerchant_external_id)
                ], limit=1)
                if partner_bank and partner_bank.partner_id:
                    escrow_type = partner_bank.partner_id.paylox_escrow_type

            if not escrow_type and basket.partner_id:
                escrow_type = basket.partner_id.paylox_escrow_type

            if not escrow_type and basket.transaction_id and basket.transaction_id.partner_id:
                escrow_type = basket.transaction_id.partner_id.paylox_escrow_type

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

    def _action_approve(self):
        res = super()._action_approve()
        self._escrow_trigger_auto_approval()
        return res

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

    def _escrow_trigger_auto_approval(self):
        stack = set(self.env.context.get('escrow_auto_chain_stack', []))
        for basket in self:
            company = basket.transaction_id.company_id
            if (not basket.transaction_id or company.system != 'escrow' or
                    basket.approval_state != '+' or not basket.paylox_escrow_type):
                continue

            if basket.paylox_escrow_type in stack:
                continue

            child_types = company._get_escrow_chain_children(basket.paylox_escrow_type)
            if not child_types:
                continue
            raise Exception(basket.transaction_id.paylox_basket_ids)
            dependents = basket.transaction_id.paylox_basket_ids.filtered(lambda b: b.paylox_escrow_type in child_types and b.approval_state != '+')
            if not dependents:
                continue

            new_stack = list(stack | {basket.paylox_escrow_type})
            try:
                dependents.with_context(escrow_auto_chain_stack=new_stack).sudo()._action_approve()
            except Exception as err:  # pragma: no cover - logging safeguard
                _logger.exception('Failed to auto-approve cascaded escrow basket(s): %s', err)

    def _escrow_visibility_domain(self):
        user = self.env.user
        if not user._is_restricted_escrow_user():
            return []

        company_map = user._get_escrow_allowed_type_map()
        domain_parts = []
        for company_id, types in company_map.items():
            if not types:
                continue
            domain_parts.append([
                ('transaction_id.company_id', '=', company_id),
                ('paylox_escrow_type', 'in', list(types)),
            ])

        if not domain_parts:
            domain_parts.append([
                ('paylox_escrow_type', 'in', list(ESCROW_DEFAULT_VISIBLE_TYPES)),
            ])

        visibility_domain = expression.OR(domain_parts)
        return expression.OR([
            [('transaction_id.company_id.system', '!=', 'escrow')],
            visibility_domain,
        ])

    @api.model
    def _apply_escrow_visibility_domain(self, domain):
        base_domain = domain or []
        visibility_domain = self._escrow_visibility_domain()

        if base_domain and visibility_domain:
            return expression.AND([base_domain, visibility_domain])
        if base_domain:
            return base_domain
        if visibility_domain:
            return visibility_domain
        return []

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        args = self._apply_escrow_visibility_domain(args)
        return super().search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = self._apply_escrow_visibility_domain(domain)
        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    def check_access_rule(self, operation):
        super().check_access_rule(operation)
        user = self.env.user
        if not user._is_restricted_escrow_user():
            return

        company_map = user._get_escrow_allowed_type_map()
        restricted = self.filtered(lambda b: b.transaction_id and b.transaction_id.company_id.system == 'escrow' and b.paylox_escrow_type not in company_map.get(b.transaction_id.company_id.id, b.transaction_id.company_id._get_escrow_allowed_types_for_user(user)))
        if restricted:
            raise AccessError(_('You do not have the required rights to access these escrow transfers.'))
