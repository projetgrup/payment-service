# -*- coding: utf-8 -*-
from odoo import fields, models, _

class PaymentAcquirerJetcheckoutApiPos(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.pos'
    _description = 'Jetcheckout Pos'

    acquirer_id = fields.Many2one('payment.acquirer')
    application_ids = fields.Many2many('payment.acquirer.jetcheckout.api.application', 'payment_jetcheckout_api_application_pos_rel', 'pos_id', 'application_id', string='Applications', ondelete='cascade')
    campaign_ids = fields.One2many('payment.acquirer.jetcheckout.api.campaign', 'pos_id', 'Campaigns')
    parent_id = fields.Many2one('payment.acquirer.jetcheckout.api.poses')
    res_id = fields.Integer(readonly=True)
    name = fields.Char('Name')
    provider_id = fields.Many2one('payment.acquirer.jetcheckout.provider', readonly=True)
    is_active = fields.Boolean('Active', default=True)
    is_client_active = fields.Boolean(readonly=True)
    is_merchant_active = fields.Boolean(readonly=True)
    is_apikey_active = fields.Boolean(readonly=True)
    is_terminal_active = fields.Boolean(readonly=True)
    is_username_active = fields.Boolean(readonly=True)
    is_password_active = fields.Boolean(readonly=True)
    is_refid_active = fields.Boolean(readonly=True)
    is_rfnd_username_active = fields.Boolean(readonly=True)
    is_rfnd_password_active = fields.Boolean(readonly=True)
    client_id = fields.Char('Client ID')
    merchant_id = fields.Char('Merchant ID')
    terminal_id = fields.Char('Terminal ID')
    api_key = fields.Char('API Key')
    secret_key = fields.Char('Secret Key')
    username = fields.Char('Username')
    password = fields.Char('Password')
    rfnd_username = fields.Char('Refund Username')
    rfnd_password = fields.Char('Refund Password')
    ref_id = fields.Char('Ref ID')
    priority = fields.Char('Priority')
    usage_3d = fields.Selection([('Not Usable','Not Usable'),('Choosable','Choosable'),('Mandatory','Mandatory')], string='3D Usage')
    mode = fields.Selection([('P','Production'),('T','Test')], string='Mode')
    notes = fields.Text('Notes', readonly=True)

    customer_ip = fields.Char()
    customer_email = fields.Char()
    customer_name = fields.Char()
    customer_surname = fields.Char()
    customer_address = fields.Char()
    customer_phone = fields.Char()
    customer_id = fields.Char()
    customer_identity = fields.Char()
    customer_city = fields.Char()
    customer_country = fields.Char()
    customer_postal_code = fields.Char()
    customer_company = fields.Char()
    basket_item_id = fields.Char()
    basket_item_name = fields.Char()
    basket_item_desc = fields.Char()
    basket_item_categ = fields.Char()
    billing_address_contact = fields.Char()
    billing_address = fields.Char()
    billing_address_city = fields.Char()
    billing_address_country = fields.Char()
    shipping_address_contact = fields.Char()
    shipping_address = fields.Char()
    shipping_address_city = fields.Char()
    shipping_address_country = fields.Char()

    def write(self, vals):
        values = {key: vals[key] for key in (
            'name',
            'is_active',
            'client_id',
            'merchant_id',
            'terminal_id',
            'api_key',
            'secret_key',
            'username',
            'username',
            'password',
            'rfnd_username',
            'rfnd_password',
            'ref_id',
            'priority',
            'usage_3d',
            'mode',
            'customer_ip',
            'customer_email',
            'customer_name',
            'customer_surname',
            'customer_address',
            'customer_phone',
            'customer_id',
            'customer_identity',
            'customer_city',
            'customer_country',
            'customer_postal_code',
            'customer_company',
            'basket_item_id',
            'basket_item_name',
            'basket_item_desc',
            'basket_item_categ',
            'billing_address_contact',
            'billing_address',
            'billing_address_city',
            'billing_address_country',
            'shipping_address_contact',
            'shipping_address',
            'shipping_address_city',
            'shipping_address_country',
        ) if key in vals}
        if values:
            self.acquirer_id._rpc('jet.virtual.pos', 'write', self.res_id, values)
        return super().write(vals)

class PaymentAcquirerJetcheckoutApiPoses(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.poses'
    _description = 'Jetcheckout Poses'

    acquirer_id = fields.Many2one('payment.acquirer')
    pos_ids = fields.One2many('payment.acquirer.jetcheckout.api.pos', 'parent_id', 'Poses')
