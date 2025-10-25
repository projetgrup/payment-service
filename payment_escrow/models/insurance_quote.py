# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class EscrowInsuranceQuote(models.Model):
    _name = 'escrow.insurance.quote'
    _description = 'Insurance Quote Request'
    _order = 'create_date desc'
    _rec_name = 'plate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Personal Information
    birth_date = fields.Date(string='Birth Date', required=True)
    vat = fields.Char(string='T.C. Identity Number', size=11, required=True)
    mobile = fields.Char(string='Mobile Number', required=True)
    email = fields.Char(string='Email', required=True)

    # Vehicle Information
    plate = fields.Char(string='License Plate', required=True)
    license_no = fields.Char(string='License Serial Number', size=10, required=True)
    chassis_no = fields.Char(string='Chassis Number', size=17, required=True)
    engine_no = fields.Char(string='Engine Number')
    registration_date = fields.Date(string='Registration Date')
    model = fields.Char(string='Vehicle Model', required=True)
    year = fields.Char(string='Model Year', size=4, required=True)

    # System Fields
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Customer')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('quoted', 'Quoted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    notes = fields.Text(string='Notes')
    quote_amount = fields.Monetary(string='Quote Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    def action_set_sent(self):
        self.write({'state': 'sent'})

    def action_set_quoted(self):
        self.write({'state': 'quoted'})

    def action_set_rejected(self):
        self.write({'state': 'rejected'})

    def action_set_cancelled(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_submit_quote(self):
        for record in self:
            record.action_set_sent()
            user = record.env.user
            company = record.company_id
            result, message = self.env['syncops.connector'].sudo()._execute(
                'insurance_post_vehicle_quote', 
                reference=str(user.partner_id.id), 
                params={
                    'birth_date': record.birth_date,
                    'vat': record.vat,
                    'mobile': record.mobile,
                    'email': record.email,
                    'plate': record.plate,
                    'license_no': record.license_no,
                    'chassis_no': record.chassis_no,
                    # 'engine_no': record.engine_no,
                    # 'registration_date': record.registration_date,
                    'model': record.model,
                    'year': record.year,
                }, 
                company=company, 
                message=True
            )
            if not result:
                raise Exception(_('Failed to submit insurance quote: %s') % message)
            
            record.action_set_quoted()
            
