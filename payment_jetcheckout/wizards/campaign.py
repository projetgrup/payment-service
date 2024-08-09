# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class PaymentPayloxCampaign(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.campaigns'
    _description = 'Paylox Campaigns'

    acquirer_id = fields.Many2one('payment.acquirer')
    line_ids = fields.One2many('payment.acquirer.jetcheckout.api.campaigns.line', 'parent_id')


class PaymentPayloxCampaignLine(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.campaigns.line'
    _description = 'Paylox Campaign Lines'
    _order = 'name'

    acquirer_id = fields.Many2one('payment.acquirer')
    parent_id = fields.Many2one('payment.acquirer.jetcheckout.api.campaigns', ondelete='cascade')
    campaign_id = fields.Many2one('payment.acquirer.jetcheckout.campaign')
    name = fields.Char()
    is_active = fields.Boolean('Active')

    def select(self):
        self.parent_id.acquirer_id.jetcheckout_campaign_id = self.campaign_id.id


class PaymentPayloxApiCampaign(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.campaign'
    _description = 'Paylox API Campaigns'
    _remote_name = 'jet.pos.price'

    acquirer_id = fields.Many2one('payment.acquirer')
    application_id = fields.Many2one('payment.acquirer.jetcheckout.api.application')
    virtual_pos_id = fields.Many2one('payment.acquirer.jetcheckout.api.pos')
    res_id = fields.Integer(readonly=True)
    offer_name = fields.Char('Campaign Name', required=True)
    currency_id = fields.Many2one('payment.acquirer.jetcheckout.api.currency', required=True, ondelete='cascade')
    is_active = fields.Boolean('Active', default=True)
    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')
    card_family_names = fields.Char('Card Family Names', readonly=True)
    installments = fields.Char('Installments', readonly=True)
    pos_lines = fields.One2many('payment.acquirer.jetcheckout.api.installment', 'pos_price_id', 'Lines')
    card_filters = fields.Many2many('payment.acquirer.jetcheckout.api.family', 'payment_jetcheckout_api_campaing_family_rel', 'campaign_id', 'family_id', string='Card Families', ondelete='cascade', domain='[("acquirer_id", "=", acquirer_id)]')
    excluded_bins = fields.Many2many('payment.acquirer.jetcheckout.api.excluded', 'payment_jetcheckout_api_campaing_excluded_rel', 'campaign_id', 'excluded_id', string='Excluded Bins', ondelete='cascade', domain='[("acquirer_id", "=", acquirer_id)]')
    imported = fields.Boolean(default=False, readonly=True)
    import_rates = fields.Boolean(related='virtual_pos_id.import_rates')


class PaymentPayloxApiInstallment(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.installment'
    _description = 'Paylox API Installments'
    _remote_name = 'jet.pos.price.line'

    @api.depends('fixed_customer_rate')
    def _compute_customer_rate_active(self):
        for rec in self:
            rec.customer_rate_active = False
            if rec.fixed_customer_rate:
                rec.customer_rate_active = True
            else:
                rec.customer_rate_active = True

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
        ('13', '13'),
        ('14', '14'),
        ('15', '15'),
        ('16', '16'),
        ('17', '17'),
        ('18', '18'),
        ('19', '19'),
        ('20', '20'),
        ('21', '21'),
        ('22', '22'),
        ('23', '23'),
        ('24', '24'),
        ('25', '25'),
        ('26', '26'),
        ('27', '27'),
        ('28', '28'),
        ('29', '29'),
        ('30', '30'),
        ('31', '31'),
        ('32', '32'),
        ('33', '33'),
        ('34', '34'),
        ('35', '35'),
        ('36', '36'),
    ], string='Installment Count', required=True)
    customer_rate = fields.Float('Customer Rate')
    cost_rate = fields.Float('Cost Rate')
    additional_rate = fields.Float('Additional Rate')
    margin_rate = fields.Float('Margin Rate')
    fixed_customer_rate = fields.Boolean('Fixed Customer Rate')
    only_fundings_active = fields.Boolean('Only Fundings Active')
    min_amount = fields.Integer('Minimum Amount')
    max_amount = fields.Integer('Maximum Amount')
    is_active = fields.Boolean('Active', default=True)
    plus_installment = fields.Integer('Plus Installment')
    plus_installment_description = fields.Char('Plus Installment Description')
    imported = fields.Boolean(related='pos_price_id.imported')
    calc_cust_rates = fields.Boolean(related='pos_price_id.virtual_pos_id.calc_cust_rates')
    customer_rate_active = fields.Boolean(compute='_compute_customer_rate_active')

    @api.onchange('cost_rate', 'additional_rate', 'margin_rate', 'only_fundings_active')
    def _onchange_rates(self):
        if self.calc_cust_rates or self.campaign_id != False:
            base_amount = 100 - (self.cost_rate - self.additional_rate)
            cost_amount = self.cost_rate - self.additional_rate

            customer_rate = 0
            if cost_amount > 0:
                customer_rate = float((cost_amount * 100) / base_amount)

            if customer_rate < self.margin_rate:
                customer_rate = 0

            if self.campaign_id != False:
                if self.cost_rate > 0:
                    self.is_active = True
                else:
                    self.is_active = False
                
                if customer_rate > 0 and self.only_fundings_active:
                    self.is_active = False

                if self.fixed_customer_rate:
                    if not self.is_active:
                        self.fixed_customer_rate = False
                        self.customer_rate = customer_rate
                else:
                    self.customer_rate = customer_rate
            else:
                if not self.fixed_customer_rate:
                    self.customer_rate = customer_rate


class PaymentPayloxApiFamily(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.family'
    _description = 'Paylox API Credit Card Family'
    _order = 'name'
    _remote_name = 'jet.card.family'

    def _compute_preview(self):
        for family in self:
            if family.logo:
                family.preview = '<img src="%s"/>' % family.logo
            else:
                family.preview = False

    acquirer_id = fields.Many2one('payment.acquirer')
    res_id = fields.Integer(readonly=True)
    name = fields.Char(readonly=True)
    logo = fields.Char(readonly=True)
    preview = fields.Html(compute='_compute_preview', readonly=True, sanitize=False)


class PaymentPayloxApiBank(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.bank'
    _description = 'Paylox API Banks'
    _remote_name = 'jet.bank'

    acquirer_id = fields.Many2one('payment.acquirer')
    res_id = fields.Integer(readonly=True)
    name = fields.Char(readonly=True)

class PaymentPayloxApiExcluded(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.excluded'
    _description = 'Paylox API Excluded Bins'
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
