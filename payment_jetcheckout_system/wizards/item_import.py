# -*- coding: utf-8 -*-
import xlrd
import base64
from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PaymentItemImport(models.TransientModel):
    _name = 'payment.item.import'
    _description = 'Payment Item Import'

    file = fields.Binary()
    filename = fields.Char()
    line_ids = fields.One2many('payment.item.import.line', 'wizard_id', 'Lines', readonly=True)

    def _cast_to_string(self, value):
        if isinstance(value, float):
            value = str(value)
            if value.endswith('.0'):
                value = value[:-2]
        return value

    def _get_date(self, value):
        if value:
            try:
                return datetime.strptime(value, '%Y-%m-%d')
            except:
                return datetime(*xlrd.xldate_as_tuple(value, 0))
        return value

    def _get_row(self, value):
        return {
            'partner_name': value['Partner Name'],
            'partner_vat': value.get('Partner VAT', False),
            'partner_ref': value.get('Partner Reference', False),
            'partner_email': value.get('Partner Email', False),
            'partner_street': value.get('Partner Street', False),
            'partner_tax_office': value.get('Partner Tax Office', False),
            'amount': float(value['Amount']),
            'date': self._get_date(value.get('Date', False)),
            'due_date': self._get_date(value.get('Due Date', False)),
            'ref': value.get('Reference', False),
            'tag': value.get('Tag', False),
            'bank_iban': value.get('Bank IBAN', False),
            'bank_holder': value.get('Bank Holder Name', False),
            'bank_merchant': value.get('Bank Merchant Name', False),
            'description': self._cast_to_string(value.get('Description', False)),
            'user_name': value.get('Sales Representative Name', False),
            'user_email': value.get('Sales Representative Email', False),
            'user_mobile': self._cast_to_string(value.get('Sales Representative Mobile', False)),
        }

    def _prepare_row(self, line):
        company = line.company_id
        partner_field = company._get_payment_partner_unique_field()
        partner = self.env['res.partner'].search([
            (partner_field, '=', getattr(line, 'partner_%s' % partner_field)),
            ('parent_id', '=', False),
            ('system', '=', company.system),
            '|', ('company_id', '=', company.id),
                 ('company_id.parent_id', '=', company.id),
        ], limit=1)
        if partner and partner.company_id:
            company = partner.company_id

        if line.user_email:
            user_values = {}
            if line.user_name:
                user_values.update({'name': line.user_name})
            if line.user_mobile:
                user_values.update({
                    'phone': line.user_mobile,
                    'mobile': line.user_mobile
                })
            parent = company.partner_id

            user = self.env['res.users'].search([('login', '=', line.user_email)], limit=1)
            if user:
                if user.parent_id.id != parent.id:
                    user_values.update({'parent_id': parent.id})
                user_entries = user.read(list(user_values.keys()), load=None)[0]
                user_values = {key: val for key, val in user_values.items() if user_entries[key] != val}
                if user_values:
                    user.write(user_values)
            else:
                user_values.update({
                    'name': user_values.get('name', line.user_email),
                    'login': line.user_email,
                    'parent_id': parent.id,
                    'company_id': company.id,
                    'company_ids': [(4, company.id)],
                })
                user = self.env['res.users'].create(user_values)
        else:
            user = False

        partner_values = {'user_id': user and user.id}
        if line.partner_vat:
            partner_values.update({'vat': line.partner_vat})
        if line.partner_ref:
            partner_values.update({'ref': line.partner_ref})
        if line.partner_name:
            partner_values.update({'name': line.partner_name})
        if line.partner_email:
            partner_values.update({'email': line.partner_email})
        if line.partner_street:
            partner_values.update({'street': line.partner_street})
        if line.partner_tax_office:
            partner_values.update({'paylox_tax_office': line.partner_tax_office})
        if partner:
            partner_entries = partner.read(list(partner_values.keys()), load=None)[0]
            partner_values = {key: val for key, val in partner_values.items() if partner_entries[key] != val}
            if partner_values:
                partner.write(partner_values)
        else:
            partner_values.update({
                'vat': line.partner_vat,
                'ref': line.partner_ref,
                'system': company.system,
                'company_id': company.id,
            })
            partner = partner.create(partner_values)

        bank = False
        bank_token = False
        bank_token_ok = company.payment_item_bank_token_ok
        if line.bank_iban:
            bank = partner.bank_ids.filtered(lambda b: b.acc_number == line.bank_iban)
            if bank:
                if bank_token_ok:
                    bank.write({
                        'acc_holder_name': line.bank_holder,
                    })
                    bank_token = bank.api_token_ids.create({
                        'partner_bank_id': bank.id,
                        'api_merchant': line.bank_merchant,
                    })
                else:
                    bank.write({
                        'acc_holder_name': line.bank_holder,
                        'api_merchant': line.bank_merchant,
                    })
            else:
                if bank_token_ok:
                    bank = bank.create({
                        'partner_id': partner.id,
                        'acc_holder_name': line.bank_holder,
                    })
                    bank_token = bank.api_token_ids.create({
                        'partner_bank_id': bank.id,
                        'api_merchant': line.bank_merchant,
                    })
                else:
                    partner.bank_ids = [(0, 0, {
                        'acc_number': line.bank_iban,
                        'acc_holder_name': line.bank_holder,
                        'api_merchant': line.bank_merchant,
                    })]

        return {
            'parent_id': partner.id,
            'amount': line.amount,
            'date': line.date,
            'due_date': line.due_date,
            'ref': line.ref,
            'tag': line.tag,
            'description': line.description,
            'system': company.system,
            'company_id': company.id,
            'currency_id': line.currency_id.id,
            'bank_id': bank_token_ok and bank and bank.id or False,
            'bank_token_id': bank_token_ok and bank_token and bank_token.id or False,
        }

    @api.onchange('file')
    def onchange_file(self):
        if self.file:
            data = base64.b64decode(self.file)
            wb = xlrd.open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            values = []
            cols = []
            for i in range(sheet.nrows):
                row = sheet.row_values(i)
                if not i:
                    cols = row
                    if not 'Partner Name' in cols:
                        raise UserError(_('Please create a "Partner Name" column'))
                    if not 'Partner VAT' in cols:
                        raise UserError(_('Please create a "Partner VAT" column'))
                    if not 'Partner Email' in cols:
                        raise UserError(_('Please create a "Partner Email" column'))
                    elif not 'Amount' in cols:
                        raise UserError(_('Please create a "Amount" column'))
                else:
                    val = dict(zip(cols, row))
                    if isinstance(val['Partner VAT'], float):
                        val['Partner VAT'] = '%.0f' % val['Partner VAT']
                    vals = self._get_row(val)
                    if 'Currency' in val:
                        currency = self.env['res.currency'].search([('name', '=', val['Currency'])], limit=1)
                        if currency:
                            vals['currency_id'] = currency.id
                    if 'Company' in val:
                        company = self.env['res.company'].search([('name', '=', val['Company'])], limit=1)
                        if company:
                            vals['company_id'] = company.id
                    values.append(vals)
            self.line_ids = [(5, 0, 0)] + [(0, 0, value) for value in values]

        else:
            self.line_ids = [(5, 0, 0)]

    def confirm(self):
        items = self.env['payment.item']
        for line in self.line_ids:
            row = self._prepare_row(line)
            items.create(row)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class PaymentItemImportLine(models.TransientModel):
    _name = 'payment.item.import.line'
    _description = 'Payment Item Import Line'

    wizard_id = fields.Many2one('payment.item.import')
    partner_id = fields.Many2one('res.partner', readonly=True)
    partner_name = fields.Char('Partner Name', readonly=True)
    partner_vat = fields.Char('Partner VAT', readonly=True)
    partner_ref = fields.Char('Partner Reference', readonly=True)
    partner_email = fields.Char('Partner Email', readonly=True)
    partner_street = fields.Char('Partner Street', readonly=True)
    partner_tax_office = fields.Char('Partner Tax Office', readonly=True)
    amount = fields.Monetary('Amount', readonly=True)
    date = fields.Date('Date', readonly=True)
    due_date = fields.Date('Due Date', readonly=True)
    ref = fields.Char('Reference', readonly=True)
    tag = fields.Char('Tag', readonly=True)
    bank_iban = fields.Char('IBAN', readonly=True)
    bank_holder = fields.Char('Account Holder', readonly=True)
    bank_merchant = fields.Char('Merchant', readonly=True)
    user_id = fields.Many2one('res.users', 'Sales Representative', readonly=True)
    user_name = fields.Char('Sales Representative Name', readonly=True)
    user_email = fields.Char('Sales Representative Email', readonly=True)
    user_mobile = fields.Char('Sales Representative Mobile', readonly=True)
    description = fields.Char('Description', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True, required=True, default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', readonly=True, required=True, default=lambda self: self.env.company)
