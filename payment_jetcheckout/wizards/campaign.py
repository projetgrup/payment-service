# -*- coding: utf-8 -*-
from odoo import fields, models, _

class PaymentAcquirerJetcheckoutApiCampaigns(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.campaigns'
    _description = 'Jetcheckout API Campaigns'

    acquirer_id = fields.Many2one('payment.acquirer')
    line_ids = fields.One2many('payment.acquirer.jetcheckout.api.campaigns.line', 'parent_id')


class PaymentAcquirerJetcheckoutApiCampaignsLine(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.campaigns.line'
    _description = 'Jetcheckout API Campaigns Line'
    _order = 'name'

    acquirer_id = fields.Many2one('payment.acquirer')
    parent_id = fields.Many2one('payment.acquirer.jetcheckout.api.campaigns', ondelete='cascade')
    campaign_id = fields.Many2one('payment.acquirer.jetcheckout.campaign')
    name = fields.Char()
    is_active = fields.Boolean('Active')

    def select(self):
        self.parent_id.acquirer_id.jetcheckout_campaign_id = self.campaign_id.id


class PaymentAcquirerJetcheckoutApiCampaign(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.campaign'
    _description = 'Jetcheckout API Campaign'
    _remote_name = 'jet.pos.price'

    acquirer_id = fields.Many2one('payment.acquirer')
    application_id = fields.Many2one('payment.acquirer.jetcheckout.api.application')
    virtual_pos_id = fields.Many2one('payment.acquirer.jetcheckout.api.pos')
    res_id = fields.Integer(readonly=True)
    offer_name = fields.Char('Campaign Name', required=True)
    currency_id = fields.Many2one('payment.acquirer.jetcheckout.api.currency', required=True)
    is_active = fields.Boolean('Active', default=True)
    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')
    card_family_names = fields.Char('Card Family Names', readonly=True)
    installments = fields.Char('Installments', readonly=True)
    pos_lines = fields.One2many('payment.acquirer.jetcheckout.api.installment', 'pos_price_id', 'Lines')
    card_families = fields.Many2many('payment.acquirer.jetcheckout.api.family', 'payment_jetcheckout_api_campaing_family_rel', 'campaign_id', 'family_id', string='Card Families', ondelete='cascade')
    excluded_bins = fields.Many2many('payment.acquirer.jetcheckout.api.excluded', 'payment_jetcheckout_api_campaing_excluded_rel', 'campaign_id', 'excluded_id', string='Excluded Bins', ondelete='cascade')


class PaymentAcquirerJetcheckoutApiInstallment(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.installment'
    _description = 'Jetcheckout API Installment'
    _remote_name = 'jet.pos.price.line'

    acquirer_id = fields.Many2one('payment.acquirer')
    res_id = fields.Integer(readonly=True)
    pos_price_id = fields.Many2one('payment.acquirer.jetcheckout.api.campaign')
    installment_type = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
    ], string='Installment Count', required=True)
    customer_rate = fields.Float('Customer Rate')
    cost_rate = fields.Float('Cost Rate')
    additional_rate = fields.Float('Additional Rate')
    fixed_customer_rate = fields.Boolean('Fixed Customer Rate')
    min_amount = fields.Integer('Minimum Amount')
    max_amount = fields.Integer('Maximum Amount')
    is_active = fields.Boolean('Active', default=True)
    plus_installment = fields.Integer('Plus Installment')
    plus_installment_description = fields.Char('Plus Installment Description')

class PaymentAcquirerJetcheckoutApiFamily(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.family'
    _description = 'Jetcheckout API Family'
    _order = 'name'
    _remote_name = 'jet.card.family'

    acquirer_id = fields.Many2one('payment.acquirer')
    res_id = fields.Integer(readonly=True)
    name = fields.Char(readonly=True)
    logo = fields.Char(readonly=True)

class PaymentAcquirerJetcheckoutApiBank(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.bank'
    _description = 'Jetcheckout API Bank'
    _remote_name = 'jet.bank'

    acquirer_id = fields.Many2one('payment.acquirer')
    res_id = fields.Integer(readonly=True)
    name = fields.Char(readonly=True)

class PaymentAcquirerJetcheckoutApiExcluded(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.excluded'
    _description = 'Jetcheckout API Excluded Bins'
    _remote_name = 'jet.bin'

    acquirer_id = fields.Many2one('payment.acquirer')
    res_id = fields.Integer(readonly=True)
    code = fields.Char(readonly=True)
    card_family_id = fields.Many2one('payment.acquirer.jetcheckout.api.family', string='Card Family', readonly=True)
    bank_code = fields.Many2one('payment.acquirer.jetcheckout.api.bank', string='Bank Name', readonly=True)
    card_type = fields.Selection([
        ('Credit', 'Credit'),
        ('Debit', 'Debit'),
        ('Prepaid', 'Prepaid'),
        ('Credit-Business', 'Credit-Business'),
        ('Debit-Business', 'Debit-Business'),
        ('Prepaid-Business', 'Prepaid-Business'),
    ], string='Card Type', readonly=True)
    mandatory_3d = fields.Boolean('3D Mandatory', readonly=True)
    program = fields.Selection([
        ('Amex', 'Amex'),
        ('JCB', 'JCB'),
        ('Mastercard', 'Mastercard'),
        ('TROY', 'TROY'),
        ('UnionPay', 'UnionPay'),
        ('VISA', 'VISA'),
    ], string='Program', readonly=True)
