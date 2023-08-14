# -*- coding: utf-8 -*-
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
    type_item_subtype = fields.Selection([('balance', 'Current Balances'), ('invoice', 'Unpaid Invoices')])
    type_item_subtype_ok = fields.Boolean(compute='_compute_type_item_subtype_ok')

    def _show_options(self):
        res = super()._show_options()
        if self.type == 'partner':
            return False
        elif self.type == 'item':
            return True
        return res

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

        if res['type'] == 'item':
            res['type_item_subtype'] = 'balance'

        return res
    
    def confirm(self):
        res = super().confirm()

        if self.type == 'partner':
            lines = self.env['syncops.connector']._execute('payment_get_partner_list', params={
                'company_id': self.env.company.partner_id.ref,
            })
            if not lines:
                lines = []

            self.line_ids = [(0, 0, {
                'name': line.get('name', False),
                'partner_vat': line.get('vat', False),
                'partner_ref': line.get('ref', False),
                'partner_email': line.get('email', False),
                'partner_phone': line.get('phone', False),
            }) for line in lines]
            res['view_id'] = self.env.ref('payment_syncops.tree_wizard_sync_line_partner').id

        elif self.type == 'item':
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
                res['view_id'] = self.env.ref('payment_syncops.tree_wizard_sync_line_item_balance').id

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
                res['view_id'] = self.env.ref('payment_syncops.tree_wizard_sync_line_item_invoice').id

        return res

    def sync(self):
        res = super().sync()
        wizard = self.browse(self.env.context.get('wizard_id', 0))
        if wizard:
            company = self.env.company
            partners_all = self.env['res.partner']
            partners = partners_all.search_read([
                ('company_id', '=', company.id),
                ('vat', 'in', wizard.line_ids.mapped('partner_vat'))
            ], ['id', 'vat'])
            partners = {partner['vat']: partner['id'] for partner in partners}
            if wizard.type == 'partner':
                for line in wizard.line_ids.read():
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
                            'system': wizard.system or company.system,
                            'name': line['name'],
                            'vat': line['partner_vat'],
                            'ref': line['partner_ref'],
                            'email': line['partner_email'],
                            'phone': line['partner_phone'],
                            'mobile': line['partner_phone'],
                            'company_id': company.id,
                        })
            elif wizard.type == 'item':
                items_all = self.env['payment.item']
                if wizard.type_item_subtype == 'balance':
                    items = items_all.search_read([
                        ('company_id', '=', company.id),
                        ('paid', '=', False),
                        ('vat', 'in', wizard.line_ids.mapped('partner_vat')),
                        ('system', '=', wizard.system),
                    ], ['id', 'parent_id'])

                    items = {item['parent_id'][0]: item['id'] for item in items}
                    for line in wizard.line_ids.read():
                        if line['partner_vat'] in partners and partners[line['partner_vat']] in items:
                            items_all.browse(items[partners[line['partner_vat']]]).write({
                                'amount': line['partner_balance'],
                            })
                        else:
                            if line['partner_vat'] in partners:
                                partner = partners_all.browse(partners[line['partner_vat']])
                            else:
                                partner = partners_all.create({
                                    'system': wizard.system or company.system,
                                    'name': line['name'],
                                    'vat': line['partner_vat'],
                                    'ref': line['partner_ref'],
                                    'email': line['partner_email'],
                                    'phone': line['partner_phone'],
                                    'mobile': line['partner_phone'],
                                    'company_id': company.id,
                                })
                            items_all.create({
                                'system': wizard.system or company.system,
                                'amount': line['partner_balance'],
                                'parent_id': partner.id,
                                'company_id': company.id,
                                'currency_id': line['currency_id'] and line['currency_id'][0] or company.currency_id.id,
                            })
                elif wizard.type_item_subtype == 'invoice':
                    items = items_all.search_read([
                        ('company_id', '=', company.id),
                        ('paid', '=', False),
                        ('vat', 'in', wizard.line_ids.mapped('partner_vat')),
                        ('ref', 'in', wizard.line_ids.mapped('invoice_name')),
                        ('system', '=', wizard.system),
                    ], ['id', 'parent_id', 'ref'])

                    items = {f"{item['parent_id'][0]}__{item['ref']}": item['id'] for item in items}
                    for line in wizard.line_ids.read():
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
                                    'system': wizard.system or company.system,
                                    'name': line['partner_name'],
                                    'vat': line['partner_vat'],
                                    'ref': line['partner_ref'],
                                    'email': line['partner_email'],
                                    'phone': line['partner_phone'],
                                    'mobile': line['partner_mobile'],
                                    'company_id': company.id,
                                })
                            items_all.create({
                                'system': wizard.system or company.system,
                                'amount': line['invoice_amount'],
                                'description': line['invoice_name'],
                                'date': line['invoice_date'],
                                'ref': line['invoice_name'],
                                'parent_id': partner.id,
                                'company_id': company.id,
                                'currency_id': line['invoice_currency'] and line['invoice_currency'][0] or company.currency_id.id,
                            })
        return res


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
