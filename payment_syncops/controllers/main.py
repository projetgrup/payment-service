# -*- coding: utf-8 -*-
import json
import base64
from datetime import datetime

from odoo import http, fields, _
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.addons.payment_jetcheckout_system.controllers.main import JetcheckoutSystemController as JetController


class PaymentSyncopsController(JetController):

    def _jetcheckout_connector_auth(self, company, header):
        code = header.split(' ', 1)[1]
        auth = base64.b64decode(code).decode('utf-8')
        username, password = auth.split(':', 1)
        connector = request.env['syncops.connector'].sudo().search([
            ('company_id', '=', company.id),
            ('username', '=', username),
            ('token', '=', password),
        ], limit=1)
        if not connector:
            raise
        return connector
 
    def _jetcheckout_connector_get_partner_info(self, partner):
        if '__jetcheckout_partner_connector' in request.session:
            partner = request.session['__jetcheckout_partner_connector']
            return {
                'name': partner['name'],
                'vat': partner['vat'],
                'ref': partner['ref'],
                'connector': True,
            }
        else:
            partner = partner or request.env.user.sudo().partner_id
            return {
                'name': partner.name,
                'vat': partner.vat,
                'ref': partner.ref,
                'connector': False,
            }

    def _jetcheckout_connector_get_partner_balance(self, vat, ref, company=None):
        balances = []
        company = company or request.env.company
        company_id = company.sudo().partner_id.ref
        result = request.env['syncops.connector'].sudo()._execute('payment_get_partner_balance', params={
            'company_id': company_id,
            'vat': vat,
            'ref': ref,
        }, company=company)
        if result:
            for res in result:
                currency_name = res.get('currency_name', '')

                # Following two lines are for compatibility purposes
                if currency_name == 'TRL':
                    currency_name = 'TRY'

                currency = request.env['res.currency'].sudo().with_context(active_test=False).search([('name', '=', currency_name)], limit=1)
                if not currency:
                    continue

                amount = isinstance(res.get('amount'), float) and res['amount'] or 0
                amount_total = isinstance(res.get('amount_total'), float) and res['amount_total'] or 0

                balances.append({'amount': amount, 'currency': currency, 'amount_total': amount_total, 'note': res.get('note', '')})
        return balances

    def _jetcheckout_connector_get_partner_ledger(self, vat, ref, date_start, date_end, company=None):
        company = company or request.env.company
        result = request.env['syncops.connector'].sudo()._execute('payment_get_partner_ledger', params={
            'company_id': company.sudo().partner_id.ref,
            'vat': vat,
            'ref': ref,
            'date_start': date_start.strftime('%Y-%m-%d') + ' 00:00:00',
            'date_end': date_end.strftime('%Y-%m-%d') + ' 23:59:59',
        }, company=company)
        if result == None:
            return {}

        currencies = {}
        for res in result:
            currency_name = res['currency_name']

            # Following two lines are for compatibility purposes
            if currency_name == 'TRL':
                currency_name = 'TRY'

            currency = request.env['res.currency'].sudo().with_context(active_test=False).search([('name', '=', currency_name)], limit=1)
            if not currency:
                continue

            lines = [{
                'date': res['date'],
                'due_date': res['due_date'],
                'type': res['type'],
                'name': res['name'],
                'description': res['description'],
                'amount': res['amount'],
                'balance': res['balance'],
                'currency': {
                    'id' : currency.id,
                    'name' : currency.name,
                    'position' : currency.position,
                    'symbol' : currency.symbol,
                    'precision' : currency.decimal_places,
                },
            }]
            if currency_name in currencies:
                currencies[currency_name].extend(lines)
            else:
                currencies[currency_name] = lines
        return currencies

    def _jetcheckout_connector_can_show_partner_ledger(self, company=None):
        company = company or request.env.company
        return request.env['syncops.connector'].sudo()._count('payment_get_partner_ledger', company=company)

    def _jetcheckout_connector_can_show_partner_balance(self, balance):
        return bool(balance)

    def _jetcheckout_connector_can_access_partner_list(self, company=None):
        user = request.env.user.sudo()
        company = company or request.env.company
        return not user.share and company.id in user.company_ids.ids and request.env['syncops.connector'].sudo()._count('payment_get_partner_list', company=company)

    def _jetcheckout_tx_vals(self, **kwargs):
        vals = super()._jetcheckout_tx_vals(**kwargs)
        if '__jetcheckout_partner_connector' in request.session:
            partner = request.session['__jetcheckout_partner_connector']
            vals.update({
                'jetcheckout_connector_partner_name': partner['name'],
                'jetcheckout_connector_partner_vat': partner['vat'],
            })

        connector = request.env['syncops.connector'].sudo().search_count([
            ('company_id', '=', request.env.company.id),
            ('active', '=', True),
            ('connected', '=', True),
        ])
        if connector:
            vals.update({
                'jetcheckout_connector_ok': True,
            })

        return vals

    def _jetcheckout_get_data(self, acquirer=False, company=False, partner=False, transaction=False, balance=True):
        values = super()._jetcheckout_get_data(acquirer=acquirer, company=company, partner=partner, transaction=transaction, balance=balance)
        partner_connector = self._jetcheckout_connector_get_partner_info(partner)
        values['balances'] = self._jetcheckout_connector_get_partner_balance(partner_connector['vat'], partner_connector['ref'], company)
        values['show_balance'] = self._jetcheckout_connector_can_show_partner_balance(values['balances'])
        values['show_ledger'] = self._jetcheckout_connector_can_show_partner_ledger(company)
        values['show_partners'] = self._jetcheckout_connector_can_access_partner_list(company)
        values['partner_connector'] = partner_connector
        return values

    @http.route(['/my/payment/ledger'], type='http', auth='user', website=True)
    def jetcheckout_portal_payment_page_ledger(self, **kwargs):
        values = self._jetcheckout_get_data()
        year = datetime.now().year
        date_start = datetime(year, 1, 1)
        date_end = datetime(year, 12, 31)
        values.update({
            'date_start': date_start.strftime('%d-%m-%Y'),
            'date_end': date_end.strftime('%d-%m-%Y'),
            'date_format': 'DD-MM-YYYY'
        })
        return request.render('payment_syncops.payment_page_ledger', values)

    @http.route(['/my/payment/partners/ledger/list'], type='json', auth='user', website=True)
    def jetcheckout_portal_payment_page_partners_ledger_list(self, **kwargs):
        date_start = kwargs.get('start')
        if not date_start:
            return {'error': _('Start date cannot be empty')}

        date_end = kwargs.get('end')
        if not date_end:
            return {'error': _('End date cannot be empty')}

        date_format = kwargs.get('format')
        if not date_format:
            return {'error': _('Date format cannot be empty')}

        partner_connector = self._jetcheckout_connector_get_partner_info()
        vat = partner_connector['vat']
        ref = partner_connector['ref']
        date_format = date_format.replace('DD', '%d').replace('MM', '%m').replace('YYYY', '%Y')
        date_start = datetime.strptime(date_start, date_format)
        date_end = datetime.strptime(date_end, date_format)
        if date_start > date_end:
            return {'error': _('Start date cannot be later than end date')}

        rows = self._jetcheckout_connector_get_partner_ledger(vat, ref, date_start, date_end)
        ledgers = []
        for key in rows.keys():
            ledgers.extend(rows[key])

        return {
            'ledgers': ledgers
        }

    @http.route(['/my/payment/partners'], type='json', auth='user', website=True)
    def jetcheckout_portal_payment_page_partners(self, **kwargs):
        if not self._jetcheckout_connector_can_access_partner_list():
            return []

        result = request.env['syncops.connector'].sudo()._execute('payment_get_partner_list', params={
            'company_id': request.env.company.sudo().partner_id.ref,
        })
        if not result == None:
            return result
        return []

    @http.route(['/my/payment/partners/select'], type='json', auth='user', website=True)
    def jetcheckout_portal_payment_page_partners_select(self, **kwargs):
        if not self._jetcheckout_connector_can_access_partner_list():
            return False

        request.session['__jetcheckout_partner_connector'] = {
            'name': kwargs.get('company'),
            'vat': kwargs.get('vat'),
            'ref': kwargs.get('ref'),
        }

        balances = self._jetcheckout_connector_get_partner_balance(kwargs.get('vat'), kwargs.get('ref'))
        return {
            'render': request.env['ir.ui.view']._render_template('payment_syncops.payment_partner_balance', {
                'balances': balances,
                'show_balance': self._jetcheckout_connector_can_show_partner_balance(balances),
                'show_ledger': self._jetcheckout_connector_can_show_partner_ledger(),
            })
        }

    @http.route(['/my/payment/partners/reset'], type='json', auth='user', website=True)
    def jetcheckout_portal_payment_page_partners_reset(self, **kwargs):
        if '__jetcheckout_partner_connector' not in request.session:
            return False

        del request.session['__jetcheckout_partner_connector']
        partner = request.env.user.partner_id
        return {
            'name': partner.name,
            'campaign': partner.campaign_id.name,
            'render': request.env['ir.ui.view']._render_template('payment_syncops.payment_partner_balance', {
                'balances': self._jetcheckout_connector_get_partner_balance(vat=partner.vat, ref=partner.ref)
            })
        }

    @http.route(['/syncops/payment/transactions/'], type='http', auth='public', methods=['GET'], csrf=False, sitemap=False, save_session=False, website=True)
    def jetcheckout_syncops_transactions(self, **kwargs):
        headers = request.httprequest.headers
        company = request.env.company
        connector = self._jetcheckout_connector_auth(company, headers['Authorization'])
        data = json.loads(request.httprequest.get_data())
        response = json.dumps([{
            'id': 1,
            'ref': data['date'],
            'partner_ref': 'test',
            'partner_name': 'test',
            'card_6': 'test',
            'card_4': 'test',
            'vpos_id': 3,
            'bank_payment_day': 'test',
            'installment_count': 4,
            'installment_code': 'test',
            'payment_date': '2023-04-04',
            'payment_time': '11:12:32',
            'currency_code': 'test',
            'payment_amount': 123.21,
            'payment_net_amount': 235.12,
            'plus_installment': 6,
            'payment_deferral': 7,
            'bank_id': 1,
            'bank_name': 'test',
            'payment_ref': 'test',
            'refund_currency_code': 'test',
            'refund_date': '2023-03-01',
            'refund_time': '11:56:14',
            'company_code': 'test',
            'vpos_name': 'test',
        }])
        headers = [('Content-Type', 'application/json; charset=utf-8'), ('Cache-Control', 'no-store')]
        return request.make_response(response, headers)
