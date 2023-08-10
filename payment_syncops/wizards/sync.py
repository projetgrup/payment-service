# -*- coding: utf-8 -*-
import json
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class SyncopsSyncWizard(models.TransientModel):
    _inherit = 'syncops.sync.wizard'

    @api.onchange('type')
    def _compute_type_item_subtype_ok(self):
        for rec in self:
            if rec.type == 'item':
                access_partner_list = self.env['syncops.connector'].count('payment_get_partner_list')
                access_invoice_list = self.env['syncops.connector'].count('payment_get_invoice_list')
                rec.type_item_subtype_ok = access_partner_list and access_invoice_list
            else:
                rec.type_item_subtype_ok = False

    system = fields.Char()
    type_item_date_start = fields.Date()
    type_item_date_end = fields.Date()
    type_item_subtype = fields.Selection([
        ('balance', 'Current Balances'),
        ('invoice', 'Unpaid Invoices'),
    ])
    type_item_subtype_code = fields.Char()
    type_item_subtype_state = fields.Text()
    type_item_subtype_ok = fields.Boolean(compute='_compute_type_item_subtype_ok')

    @api.onchange('type_item_subtype', 'type_item_date_start', 'type_item_date_end')
    def onchange_type_item(self):
        if not self.type == 'item':
            return
        if not self.type_item_subtype_state:
            return
        state = json.loads(self.type_item_subtype_state)
        if state['type'] != self.type_item_subtype or state['start'] != self.type_item_date_start or state['end'] != self.type_item_date_end:
            self.refresh = True
        else:
            self.refresh = False

    @api.onchange('refresh')
    def onchange_refresh(self):
        if self.env.context.get('recompute'):
            if self.type_item_subtype == 'balance':
                params = {'company_id': self.env.company.partner_id.ref}
                lines = self.env['syncops.connector']._execute('payment_get_partner_list', params=params)
                if lines == None:
                    lines = []

                self.line_ids = [(5, 0, 0)] + [(0, 0, {
                    'name': line.get('name', False),
                    'partner_name': line.get('partner', False),
                    'partner_vat': line.get('vat', False),
                    'partner_ref': line.get('ref', False),
                    'partner_email': line.get('email', False),
                    'partner_phone': line.get('phone', False),
                    'partner_mobile': line.get('mobile', False),
                    'partner_balance': line.get('balance', 0),
                }) for line in lines]
                self.type_item_subtype_code = 'balance'

            elif self.type_item_subtype == 'invoice':
                params = {
                    'company': self.env.company.partner_id.ref,
                    'state': 'not_paid,posted'
                }
                if self.type_item_date_start:
                    params.update({'date_start': self.type_item_date_start.strftime(DF)})
                if self.type_item_date_end:
                    params.update({'date_end': self.type_item_date_end.strftime(DF)})

                lines = self.env['syncops.connector']._execute('payment_get_invoice_list', params=params)
                if lines == None:
                    lines = []

                currencies = self.env['res.currency'].with_context(active_test=False).search_read([], ['id', 'name'])
                currencies = {currency['name']: currency['id'] for currency in currencies}
                self.line_ids = [(5, 0, 0)] + [(0, 0, {
                    'name': line.get('partner', False),
                    'partner_name': line.get('partner', False),
                    'partner_vat': line.get('vat', False),
                    'partner_ref': line.get('ref', False),
                    'partner_email': line.get('email', False),
                    'partner_phone': line.get('phone', False),
                    'partner_mobile': line.get('mobile', False),
                    'invoice_name': line.get('name', False),
                    'invoice_date': line.get('date', False),
                    'invoice_amount': line.get('amount', 0),
                    'invoice_currency': currencies.get(line.get('currency'), False),
                }) for line in lines]
                self.type_item_subtype_code = 'invoice'
            
            self.type_item_subtype_state = json.dumps({
                'type': self.type_item_subtype,
                'start': self.type_item_date_start and self.type_item_date_start.strftime(DF),
                'end': self.type_item_date_end and self.type_item_date_end.strftime(DF),
            })

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['system'] = self.env.context.get('active_system')

        model = self.env.context.get('active_model')
        if model == 'res.partner':
            res['type'] = 'partner'
        elif model == 'payment.item':
            res['type'] = 'item'
        else:
            res['type'] = False

        if res['type'] == 'partner':
            lines = self.env['syncops.connector']._execute('payment_get_partner_list', params={
                'company_id': self.env.company.partner_id.ref,
            })
            if not lines:
                lines = []

            res['line_ids'] = [(0, 0, {
                'name': line.get('name', False),
                'partner_vat': line.get('vat', False),
                'partner_ref': line.get('ref', False),
                'partner_email': line.get('email', False),
                'partner_phone': line.get('phone', False),
            }) for line in lines]

        elif res['type'] == 'item':
            res['type_item_subtype'] = 'balance'
            res['type_item_subtype_state'] = json.dumps({
                'type': 'balance',
                'start': False,
                'end': False,
            })
            lines = self.env['syncops.connector']._execute('payment_get_partner_list', params={
                'company_id': self.env.company.partner_id.ref,
            })
            if not lines:
                lines = []

            res['line_ids'] = [(0, 0, {
                'name': line.get('name', False),
                'partner_vat': line.get('vat', False),
                'partner_ref': line.get('ref', False),
                'partner_email': line.get('email', False),
                'partner_phone': line.get('phone', False),
                'partner_balance': line.get('balance', 0),
            }) for line in lines]
        return res

    def confirm(self):
        company = self.env.company
        partners_all = self.env['res.partner']
        partners = partners_all.search_read([
            ('company_id', '=', company.id),
            ('vat', 'in', self.line_ids.mapped('partner_vat'))
        ], ['id', 'vat'])
        partners = {partner['vat']: partner['id'] for partner in partners}
        if self.type == 'partner':
            for line in self.line_ids.read():
                if line['partner_vat'] in partners:
                    partners_all.browse(partners[line['partner_vat']]).write({
                        'name': line['name'],
                        'ref': line['partner_ref'],
                        'email': line['partner_email'],
                        'phone': line['partner_phone'],
                        'mobile': line['partner_phone'],
                    })
                else:
                    partners_all.create({
                        'system': self.system or company.system,
                        'name': line['name'],
                        'vat': line['partner_vat'],
                        'ref': line['partner_ref'],
                        'email': line['partner_email'],
                        'phone': line['partner_phone'],
                        'mobile': line['partner_phone'],
                        'company_id': company.id,
                    })
        elif self.type == 'item':
            items_all = self.env['payment.item']
            if self.type_item_subtype == 'balance':
                items = items_all.search_read([
                    ('company_id', '=', company.id),
                    ('paid', '=', False),
                    ('vat', 'in', self.line_ids.mapped('partner_vat')),
                    ('system', '=', self.system),
                ], ['id', 'parent_id'])

                items = {item['parent_id'][0]: item['id'] for item in items}
                for line in self.line_ids.read():
                    if line['partner_vat'] in partners and partners[line['partner_vat']] in items:
                        items_all.browse(items[partners[line['partner_vat']]]).write({
                            'amount': line['partner_balance'],
                        })
                    else:
                        if line['partner_vat'] in partners:
                            partner = partners_all.browse(partners[line['partner_vat']])
                        else:
                            partner = partners_all.create({
                                'system': self.system or company.system,
                                'name': line['name'],
                                'vat': line['partner_vat'],
                                'ref': line['partner_ref'],
                                'email': line['partner_email'],
                                'phone': line['partner_phone'],
                                'mobile': line['partner_phone'],
                                'company_id': company.id,
                            })
                        items_all.create({
                            'system': self.system or company.system,
                            'amount': line['partner_balance'],
                            'parent_id': partner.id,
                            'company_id': company.id,
                            'currency_id': line['currency_id'] and line['currency_id'][0] or company.currency_id.id,
                        })
            elif self.type_item_subtype == 'invoice':
                items = items_all.search_read([
                    ('company_id', '=', company.id),
                    ('paid', '=', False),
                    ('vat', 'in', self.line_ids.mapped('partner_vat')),
                    ('ref', 'in', self.line_ids.mapped('invoice_name')),
                    ('system', '=', self.system),
                ], ['id', 'parent_id', 'ref'])

                items = {f"{item['parent_id'][0]}__{item['ref']}": item['id'] for item in items}
                for line in self.line_ids.read():
                    exist = line['partner_vat'] in partners
                    key = f"{partners[line['partner_vat']]}__{line['invoice_name']}" if exist else None
                    if exist and key in items:
                        items_all.browse(items[key]).write({
                            'amount': line['invoice_amount'],
                        })
                    else:
                        if exist:
                            partner = partners_all.browse(partners[line['partner_vat']])
                        else:
                            partner = partners_all.create({
                                'system': self.system or company.system,
                                'name': line['partner_name'],
                                'vat': line['partner_vat'],
                                'ref': line['partner_ref'],
                                'email': line['partner_email'],
                                'phone': line['partner_phone'],
                                'mobile': line['partner_mobile'],
                                'company_id': company.id,
                            })
                        items_all.create({
                            'system': self.system or company.system,
                            'amount': line['invoice_amount'],
                            'description': line['invoice_name'],
                            'date': line['invoice_date'],
                            'ref': line['invoice_name'],
                            'parent_id': partner.id,
                            'company_id': company.id,
                            'currency_id': line['invoice_currency'] and line['invoice_currency'][0] or company.currency_id.id,
                        })
        return super().confirm()


class SyncopsSyncWizardLine(models.TransientModel):
    _inherit = 'syncops.sync.wizard.line'

    partner_id = fields.Char(readonly=True)
    partner_name = fields.Char(readonly=True)
    partner_vat = fields.Char(readonly=True)
    partner_ref = fields.Char(readonly=True)
    partner_email = fields.Char(readonly=True)
    partner_phone = fields.Char(readonly=True)
    partner_mobile = fields.Char(readonly=True)
    partner_balance = fields.Monetary(readonly=True)
    invoice_id = fields.Char(readonly=True)
    invoice_name = fields.Char(readonly=True)
    invoice_date = fields.Date(readonly=True)
    invoice_amount = fields.Monetary(readonly=True, currency_field='invoice_currency')
    invoice_currency = fields.Many2one('res.currency', readonly=True)
