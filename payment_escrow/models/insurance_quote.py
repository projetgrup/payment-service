# -*- coding: utf-8 -*-
import logging
import time

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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
    brand_id = fields.Char(string='Brand Code')
    brand_name = fields.Char(string='Brand Name')
    model_id = fields.Char(string='Model Code')
    model_name = fields.Char(string='Model Name')
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

    @api.model
    def create_quotes(self, values):
        self = self.sudo()
        user = self.env.user
        company = self.env.company

        payload_keys = [
            'birth_date', 'vat', 'mobile', 'email', 'plate', 'license_no',
            'chassis_no', 'engine_no', 'registration_date', 'brand_id',
            'brand_name', 'model_id', 'model_name', 'year'
        ]
        payload = {'usage': '1'}
        payload.update({key: values.get(key) for key in payload_keys if values.get(key) not in (None, '')})

        result, message = self.env['syncops.connector'].sudo()._execute(
            'insurance_post_vehicle_quote',
            reference=str(user.partner_id.id),
            params=payload,
            company=company,
            message=True
        )
        if not result:
            raise ValidationError(_('Failed to submit insurance quote: %s') % message)

        response = result[0]
        success_flag = str(response.get('success', True)).lower() == 'true'
        if not success_flag:
            error_msg = response.get('message') or message or _('Failed to submit insurance quote.')
            raise ValidationError(error_msg)

        result_block = response.get('result') or {}
        quotes = []
        if isinstance(result_block, dict):
            quotes = result_block.get('quotes') or result_block.get('data') or []
        elif isinstance(result_block, list):
            quotes = result_block

        if isinstance(quotes, dict):
            quotes = [quotes]
        elif not isinstance(quotes, list):
            quotes = [quotes] if quotes else []

        def _normalize_reference(value, fallback_suffix=0):
            try:
                if value is None:
                    raise ValueError('empty reference')
                return int(str(value).strip())
            except (ValueError, TypeError):
                return int(time.time()) + fallback_suffix

        def _clone_values():
            cloned = values.copy()
            birth_date = cloned.get('birth_date')
            if isinstance(birth_date, str):
                try:
                    cloned['birth_date'] = fields.Date.to_date(birth_date)
                except ValueError:
                    pass
            return cloned

        def _parse_amount(raw):
            if raw in (None, ''):
                return None
            if isinstance(raw, (int, float)):
                return float(raw)
            if isinstance(raw, str):
                cleaned = raw.replace('.', '').replace(',', '.')
                try:
                    return float(cleaned)
                except ValueError:
                    return None
            return None

        created_records = []
        error_messages = []

        for idx, raw_entry in enumerate(quotes):
            entry = raw_entry or {}
            if not isinstance(entry, dict):
                entry = {'success': False, 'message': str(raw_entry)}

            entry_success = str(entry.get('success', True)).lower() == 'true'
            quote_info = entry.get('quote') or entry.get('data')
            if not isinstance(quote_info, dict):
                quote_info = entry if entry_success else {}

            detail_payload = entry.get('quote') or entry.get('data') or entry.get('result')
            if isinstance(detail_payload, dict):
                detail_entries = [detail_payload]
            elif isinstance(detail_payload, list):
                detail_entries = [item for item in detail_payload if isinstance(item, dict)]
            else:
                detail_entries = []

            detail_entry = detail_entries[0] if detail_entries else {}
            offer_info = detail_entry.get('teklifBilgileri') or detail_entry.get('offerInfo') or {}
            product_info = detail_entry.get('urunBilgileri') or detail_entry.get('productInfo') or {}
            company_info = detail_entry.get('sigortaSirketiBilgileri') or detail_entry.get('insuranceCompany') or {}

            reference_value = (
                offer_info.get('teklifId')
                or offer_info.get('quoteId')
                or entry.get('urun_id')
                or (quote_info.get('teklifId') if isinstance(quote_info, dict) else None)
                or (quote_info.get('quoteId') if isinstance(quote_info, dict) else None)
                or (quote_info.get('reference') if isinstance(quote_info, dict) else None)
            )
            normalized_reference = _normalize_reference(reference_value, idx)

            detail_parts = []
            if product_info.get('urunAdi'):
                detail_parts.append(_('Product: %s') % product_info.get('urunAdi'))
            elif product_info.get('urunTanimi'):
                detail_parts.append(product_info.get('urunTanimi'))

            company_label = company_info.get('tamAdi') or company_info.get('kisaAdi')
            if company_label:
                detail_parts.append(_('Company: %s') % company_label)

            start_date = offer_info.get('baslangicTarihi') or offer_info.get('startDate')
            end_date = offer_info.get('bitisTarihi') or offer_info.get('endDate')
            if start_date and end_date:
                detail_parts.append(_('Coverage: %s → %s') % (start_date, end_date))

            amount_value = None
            if entry_success:
                amount_value = (
                    _parse_amount(offer_info.get('fiyatFloat'))
                    or _parse_amount(offer_info.get('fiyat'))
                    or _parse_amount(offer_info.get('amount'))
                    or (
                        _parse_amount(quote_info.get('amount'))
                        if isinstance(quote_info, dict) else None
                    )
                    or (
                        _parse_amount(quote_info.get('price'))
                        if isinstance(quote_info, dict) else None
                    )
                )
            if amount_value is not None:
                detail_parts.append(_('Premium: %.2f') % amount_value)

            detail_message = ' | '.join([part for part in detail_parts if part])
            if not detail_message:
                if isinstance(quote_info, dict):
                    detail_message = (
                        quote_info.get('message')
                        or quote_info.get('description')
                        or quote_info.get('detail')
                    )
            if not detail_message:
                detail_message = (
                    entry.get('errorMessage')
                    or entry.get('message')
                    or entry.get('description')
                    or str(raw_entry)
                )

            create_vals = _clone_values()
            create_vals.update({
                'reference': normalized_reference,
                'quote_amount': amount_value if amount_value is not None else False,
                'quote_details': detail_message or (entry_success and _('Quote created successfully.') or _('Quote failed without details.')),
                'state': 'quoted' if entry_success else 'cancelled',
                'company_id': values.get('company_id') or company.id,
                'partner_id': values.get('partner_id'),
                'insurance_company': company_label,
            })

            created_record = self.create(create_vals)
            created_records.append({
                'id': created_record.id,
                'name': created_record.name,
                'reference': created_record.reference,
                'amount': created_record.quote_amount,
                'details': created_record.quote_details,
                'state': created_record.state,
                'success': entry_success,
            })

            if not entry_success:
                identifier = entry.get('urun_id') or reference_value
                prefix = f"[{identifier}] " if identifier else ''
                error_messages.append(f"{prefix}{detail_message or _('Unknown error')}")

        if not created_records:
            summary = '\n'.join(error_messages) if error_messages else _('No quote details returned')
            raise ValidationError(summary)

        if error_messages:
            _logger.warning('Escrow insurance quote warnings: %s', '\n'.join(error_messages))

        return created_records


