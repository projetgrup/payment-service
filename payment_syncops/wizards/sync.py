# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class SyncopsSyncWizard(models.TransientModel):
    _name = 'syncops.sync.wizard'
    _description = 'syncOPS Sync Wizard'

    system = fields.Char()
    type = fields.Char()
    count = fields.Integer(readonly=True)
    line_ids = fields.One2many('syncops.sync.wizard.line', 'wizard_id', 'Lines', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        type = res.get('type', '')
        if type == 'partner':
            lines = self.env['syncops.connector']._execute('payment_get_partner_list', params={
                'company_id': self.env.company.partner_id.ref,
            })
            if lines == None:
                lines = []

            res['line_ids'] = [(0, 0, {
                'partner_name': line.get('name', False),
                'partner_vat': line.get('vat', False),
                'partner_ref': line.get('ref', False),
                'partner_email': line.get('email', False),
                'partner_phone': line.get('phone', False),
            }) for line in lines]
            res['count'] = len(lines)

        elif type == 'item':
            lines = self.env['syncops.connector']._execute('payment_get_partner_list', params={
                'company_id': self.env.company.partner_id.ref,
            })
            if lines == None:
                lines = []

            res['line_ids'] = [(0, 0, {
                'partner_name': line.get('name', False),
                'partner_vat': line.get('vat', False),
                'partner_ref': line.get('ref', False),
                'partner_email': line.get('email', False),
                'partner_phone': line.get('phone', False),
                'partner_balance': line.get('balance', 0),
            }) for line in lines]
            res['count'] = len(lines)
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
                        'name': line['partner_name'],
                        'ref': line['partner_ref'],
                        'email': line['partner_email'],
                        'phone': line['partner_phone'],
                        'mobile': line['partner_phone'],
                    })
                else:
                    partners_all.create({
                        'vat': line['partner_vat'],
                        'name': line['partner_name'],
                        'ref': line['partner_ref'],
                        'email': line['partner_email'],
                        'phone': line['partner_phone'],
                        'mobile': line['partner_phone'],
                        'company_id': company.id,
                        'system': self.system or company.system,
                    })
        elif self.type == 'item':
            items_all = self.env['payment.item']
            items = items_all.search_read([
                ('company_id', '=', company.id),
                ('paid', '=', False),
                ('parent_id.vat', 'in', self.line_ids.mapped('partner_vat')),
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
                            'vat': line['partner_vat'],
                            'name': line['partner_name'],
                            'ref': line['partner_ref'],
                            'email': line['partner_email'],
                            'phone': line['partner_phone'],
                            'mobile': line['partner_phone'],
                            'company_id': company.id,
                            'system': self.system or company.system,
                        })
                    items_all.create({
                        'amount': line['partner_balance'],
                        'parent_id': partner.id,
                        'company_id': company.id,
                        'system': self.system or company.system,
                    })
        return {'type': 'ir.actions.act_window_close'}


class SyncopsSyncWizardLine(models.TransientModel):
    _name = 'syncops.sync.wizard.line'
    _description = 'syncOPS Sync Wizard Lines'

    wizard_id = fields.Many2one('syncops.sync.wizard')
    partner_name = fields.Char(readonly=True)
    partner_vat = fields.Char(readonly=True)
    partner_ref = fields.Char(readonly=True)
    partner_email = fields.Char(readonly=True)
    partner_phone = fields.Char(readonly=True)
    partner_balance = fields.Monetary(readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
