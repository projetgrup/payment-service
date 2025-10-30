# -*- coding: utf-8 -*-
from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    payment_page_campaign_table_ok = fields.Boolean('Campaign Table on Payment Page')
    payment_page_campaign_table_transpose = fields.Boolean('Transpose Campaign Table on Payment Page')
    payment_page_campaign_table_ids = fields.Many2many('payment.acquirer.jetcheckout.campaign', 'company_campaign_table_rel', 'company_id', 'campaign_id', string='Campaigns on Campaign Table on Payment Page')
    payment_page_campaign_table_included = fields.Boolean(string='Campaigns on Campaign Table Included on Payment Page')
    payment_page_installment_table_hide_rate = fields.Boolean(string='Hide Rate on Installment Table on Payment Page')
    payment_page_token_wo_commission = fields.Boolean(string='Payment Token Page Amount Without Commission')
    payment_page_token_view_type = fields.Selection([('select', 'Selection'), ('radio', 'Radio')], string='Payment Page Token View Type')
    payment_page_init_redirect_extra = fields.Boolean(string='Payment Page Extra Redirection Upon Payment Initialization')
    payment_page_init_warning_commission_ok = fields.Boolean(string='Payment Page Commission Warning Before Payment Initialization')
    payment_page_init_warning_commission_show_rate = fields.Boolean(string='Payment Page Commission Warning Show Rate')
    payment_page_init_warning_commission_show_calculation = fields.Boolean(string='Payment Page Commission Warning Show Calculation')
    payment_page_init_warning_commission_show_primary_advice = fields.Boolean(string='Payment Page Commission Warning Show Primary Advice')
    payment_page_init_warning_commission_show_secondary_advice = fields.Boolean(string='Payment Page Commission Warning Show Secondary Advice')
    payment_page_init_warning_commission_description = fields.Html(string='Payment Page Commission Warning Description')
    payment_page_init_popup_ok = fields.Boolean(string='Open 3D Links in Popup')
    payment_page_description_ok = fields.Boolean(string='Payment Page Description')
    payment_token_ok = fields.Boolean(string='Enable Payment Credit Card Tokens')
    payment_point_ok = fields.Boolean(string='Enable Payment Credit Card Points')
    payment_log_ok = fields.Boolean(string='Enable Logging for Payment Requests')
    payment_method_physical_pos_store_code = fields.Char(string='Payment Method Physical PoS Store Code')
    payment_method_physical_pos_ids = fields.One2many('res.company.payment.method.physicalpos', 'company_id', string='Payment Method Physical PoS List')

class CompanyPaymentMethodPhysicalpos(models.Model):
    _name = 'res.company.payment.method.physicalpos'
    _description = 'Company Payment Method Physical PoS'

    company_id = fields.Many2one('res.company')
    name = fields.Char(required=True)
    type = fields.Selection([
        ('pavo', 'Pavo'),
        ('hugin', 'Hugin'),
    ])
