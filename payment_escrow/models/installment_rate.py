# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EscrowInstallmentRate(models.Model):
    _name = 'escrow.installment.rate'
    _description = 'Escrow Installment Rate'
    _order = 'installment_count, rate'

    installment_count = fields.Selection([
        ('1', '1 Installment'),
        ('3', '3 Installments'),
        ('6', '6 Installments'),
        ('9', '9 Installments'),
        ('12', '12 Installments'),
        ('15', '15 Installments'),
        ('18', '18 Installments'),
    ], string='Installment Count', required=True, default='1')
    rate = fields.Float(string='Rate (%)', required=True, digits=(16, 6))
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Infrastructure Provider', ondelete='cascade')
    
    # Audit fields
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    create_date = fields.Datetime(string='Created on', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Updated by', readonly=True)
    write_date = fields.Datetime(string='Last Updated on', readonly=True)

    @api.constrains('installment_count')
    def _check_installment_count(self):
        for record in self:
            if not record.installment_count:
                raise ValidationError(_('Installment count is required.'))

    @api.constrains('rate')
    def _check_rate(self):
        for record in self:
            if record.rate < 0:
                raise ValidationError(_('Rate cannot be negative.'))
            if record.rate > 100:
                raise ValidationError(_('Rate cannot be greater than 100%.'))

    @api.constrains('installment_count', 'partner_id', 'company_id')
    def _check_unique_installment_count(self):
        for record in self:
            domain = [
                ('installment_count', '=', record.installment_count),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ]
            if record.partner_id:
                domain.append(('partner_id', '=', record.partner_id.id))
            else:
                domain.append(('partner_id', '=', False))
            
            existing = self.search(domain)
            if existing:
                installment_label = dict(record._fields['installment_count'].selection).get(record.installment_count)
                if record.partner_id:
                    raise ValidationError(_('An installment rate for %s already exists for this infrastructure provider.') % installment_label)
                else:
                    raise ValidationError(_('An installment rate for %s already exists for this company.') % installment_label)
