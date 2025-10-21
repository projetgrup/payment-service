# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DealerCommissionRate(models.Model):
    _name = 'dealer.commission.rate'
    _description = 'Dealer Commission Rate'
    _order = 'campaign_id, sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    partner_id = fields.Many2one('res.partner', string='Dealer', required=True)
    campaign_id = fields.Many2one('payment.acquirer.jetcheckout.campaign', string='Campaign', required=True)
    commission_rate = fields.Float(string='Commission Rate (%)', required=True, digits=(16, 2), help='Commission percentage that dealer will earn from this campaign')
    company_id = fields.Many2one('res.company', string='Company', related='partner_id.company_id', store=True, readonly=True)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('unique_partner_campaign', 
         'UNIQUE(partner_id, campaign_id)', 
         'A dealer can only have one commission rate per campaign!')
    ]

    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        for record in self:
            if record.commission_rate < 0 or record.commission_rate > 100:
                raise ValidationError(_('Commission rate must be between 0 and 100!'))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.campaign_id.name} - {record.commission_rate}%"
            result.append((record.id, name))
        return result
