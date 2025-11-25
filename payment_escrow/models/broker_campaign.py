# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EscrowBrokerCampaign(models.Model):
    _name = 'escrow.broker.campaign'
    _description = 'Broker Commission Campaign'
    _order = 'sequence, name'

    name = fields.Char(string='Campaign Name', required=True, index=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    line_ids = fields.One2many('escrow.broker.campaign.line', 'campaign_id', string='Installment Rates')
    
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    create_date = fields.Datetime(string='Created on', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Updated by', readonly=True)
    write_date = fields.Datetime(string='Last Updated on', readonly=True)

    _sql_constraints = [
        ('name_company_unique', 'unique(name, company_id)', 
         'Campaign name must be unique per company!')
    ]


class EscrowBrokerCampaignLine(models.Model):
    _name = 'escrow.broker.campaign.line'
    _description = 'Broker Campaign Installment Line'
    _order = 'installment_count'

    campaign_id = fields.Many2one('escrow.broker.campaign', string='Campaign', required=True, ondelete='cascade')
    installment_count = fields.Selection([
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
    
    broker_additional_rate = fields.Float(string='Broker Additional Rate (%)', digits=(16, 6), required=True,
                                          help='Additional commission rate for broker')
    
    _sql_constraints = [
        ('installment_campaign_unique', 'unique(campaign_id, installment_count)', 
         'Each installment count can only appear once per campaign!')
    ]

    @api.constrains('broker_additional_rate')
    def _check_broker_rate(self):
        for record in self:
            if record.broker_additional_rate < 0:
                raise ValidationError(_('Broker additional rate cannot be negative.'))
            if record.broker_additional_rate > 100:
                raise ValidationError(_('Broker additional rate cannot exceed 100%.'))
