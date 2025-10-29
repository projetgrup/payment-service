# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class EscrowInsuranceQuote(models.Model):
    _name = 'escrow.insurance.quote'
    _description = 'Insurance Quote Request'
    _order = 'create_date desc'
    _rec_name = 'plate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Personal Information
    name = fields.Char(string='Quote Name', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    birth_date = fields.Date(string='Birth Date', required=True)
    vat = fields.Char(string='T.C. Identity Number', size=11, required=True)
    mobile = fields.Char(string='Mobile Number', required=True)
    email = fields.Char(string='Email', required=True)
    person_name = fields.Char(string='Full Name', required=True)

    # Vehicle Information
    plate = fields.Char(string='License Plate', required=True)
    license_no = fields.Char(string='License Serial Number', size=10, required=True)
    chassis_no = fields.Char(string='Chassis Number', size=17)
    engine_no = fields.Char(string='Engine Number')
    registration_date = fields.Date(string='Registration Date')
    model = fields.Char(string='Vehicle Model')
    year = fields.Char(string='Model Year', size=4)

    # System Fields
    reference = fields.Integer(string='Reference', required=True, copy=False, readonly=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Customer')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('quoted', 'Quoted'),
        ('sold', 'Sold'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    notes = fields.Text(string='Notes')
    quote_amount = fields.Monetary(string='Quote Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    quote_details = fields.Text(string='Quote Details')

    # Insurance Callback Fields
    insurance_company = fields.Char(string='Insurance Company', tracking=True)
    insurance_commission = fields.Monetary(string='Insurance Commission', currency_field='currency_id', tracking=True)
    policy_pdf = fields.Binary(string='Policy PDF', attachment=True)
    policy_pdf_filename = fields.Char(string='Policy PDF Filename')
    policy_number = fields.Char(string='Policy Number', tracking=True)
    sale_date = fields.Datetime(string='Sale Date', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('escrow.insurance.quote') or _('New')
        return super(EscrowInsuranceQuote, self).create(vals)

    def action_set_sent(self):
        self.write({'state': 'sent'})

    def action_set_quoted(self):
        self.write({'state': 'quoted'})
    
    def action_set_sold(self):
        self.write({'state': 'sold'})

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
                    'birth_date': record.birth_date.strftime('%Y-%m-%d') if record.birth_date else '',
                    'vat': record.vat,
                    'mobile': record.mobile,
                    'email': record.email,
                    'plate': record.plate,
                    'license_no': record.license_no,
                    # 'chassis_no': record.chassis_no,
                    # 'engine_no': record.engine_no,
                    # 'registration_date': record.registration_date,
                    # 'model': record.model,
                    # 'year': record.year,
                }, 
                company=company, 
                message=True
            )
            if not result:
                record.quote_details = message
                record.action_set_cancelled()
                return {
                    'success': False,
                    'message': _('Failed to submit insurance quote: %s') % message
                }
            res = result[0]
            if res.get('success'):
                data = res.get('data', [])
                for item in data:
                    quote = item.get('teklifBilgileri', {})

                    record.quote_details = res.get('message', '')
                    record.reference = quote.get('teklifId', '')
                    record.action_set_sent()
                    self.env.cr.commit()
                return {
                    'success': True,
                    'message': _('Insurance quote submitted successfully.')
                }
            else:
                errors = res.get('errors', [])
                error_text = ''
                if errors:
                    if isinstance(errors, list):
                        error_text = '\n'.join(str(error) for error in errors)
                    elif isinstance(errors, str):
                        error_text = errors
                    else:
                        error_text = str(errors)
                
                message = res.get('message', 'Unknown error')
                full_message = message
                if error_text:
                    full_message = f"{message}\n{error_text}"
                    record.quote_details = full_message
                    record.action_set_cancelled()
                
                return {
                    'success': False,
                    'message': _('Insurance quote submission failed: %s') % full_message
                }
            
