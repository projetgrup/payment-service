# -*- coding: utf-8 -*-
from odoo import fields, models, _

class PaymentAcquirerJetcheckoutApiCampaign(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.campaign'
    _description = 'Jetcheckout API Campaign'

    acquirer_id = fields.Many2one('payment.acquirer')
    application_id = fields.Many2one('payment.acquirer.jetcheckout.api.application')
    pos_id = fields.Many2one('payment.acquirer.jetcheckout.api.pos')
    res_id = fields.Integer()
    offer_name = fields.Char('Campaign Name')
    currency_id = fields.Many2one('res.currency')
    is_active = fields.Boolean('Active', default=True)
    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')
    card_family_names = fields.Char('Card Family Names', readonly=True)
    installments = fields.Char('Installments', readonly=True)
    installment_ids = fields.One2many('payment.acquirer.jetcheckout.api.installment', 'campaign_id', 'Lines')
    family_ids = fields.Many2many('payment.acquirer.jetcheckout.api.family', 'payment_jetcheckout_api_campaing_family_rel', 'campaign_id', 'family_id', string='Card Families', ondelete='cascade')
    excluded_bin_ids = fields.Many2many('payment.acquirer.jetcheckout.api.excluded', 'payment_jetcheckout_api_campaing_excluded_rel', 'campaign_id', 'excluded_id', string='Excluded Bins', ondelete='cascade')

    def write(self, vals):
        values = {key: vals[key] for key in (
            'offer_name',
            'currency_id',
            'is_active',
            'from_date',
            'to_date'
        ) if key in vals}
        if values:
            self.acquirer_id._rpc('jet.pos.price', 'write', self.res_id, values)
        return super().write(vals)

class PaymentAcquirerJetcheckoutApiInstallment(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.installment'
    _description = 'Jetcheckout API Installment'

    res_id = fields.Integer()
    campaign_id = fields.Many2one('payment.acquirer.jetcheckout.api.campaign')
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
    ], string='Installment Count')
    customer_rate = fields.Float('Customer Rate')
    cost_rate = fields.Float('Cost Rate')
    is_active = fields.Boolean('Active', default=True)
    plus_installment = fields.Integer('Plus Installment')
    plus_installment_description = fields.Char('Plus Installment Description')

class PaymentAcquirerJetcheckoutApiFamily(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.family'
    _description = 'Jetcheckout API Family'

    res_id = fields.Integer()
    name = fields.Char('Name')

class PaymentAcquirerJetcheckoutApiBank(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.bank'
    _description = 'Jetcheckout API Bank'

    res_id = fields.Integer()
    name = fields.Char('Name')

class PaymentAcquirerJetcheckoutApiExcluded(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.excluded'
    _description = 'Jetcheckout API Excluded Bins'

    res_id = fields.Integer()
    name = fields.Char('Name')
    code = fields.Char('Code')
    bank_code = fields.Many2one('payment.acquirer.jetcheckout.api.bank', string='Bank Name')
    card_type = fields.Selection([
        ('Credit', 'Credit'),
        ('Debit', 'Debit'),
        ('Prepaid', 'Prepaid'),
        ('Credit-Business', 'Credit-Business'),
        ('Debit-Business', 'Debit-Business'),
        ('Prepaid-Business', 'Prepaid-Business'),
    ], string='Card Type')
    mandatory_3d = fields.Boolean('3D Mandatory')
    program = fields.Selection([
        ('Amex', 'Amex'),
        ('JCB', 'JCB'),
        ('Mastercard', 'Mastercard'),
        ('TROY', 'TROY'),
        ('UnionPay', 'UnionPay'),
        ('VISA', 'VISA'),
    ], string='Program')
