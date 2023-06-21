# -*- coding: utf-8 -*-
import io
import json
import base64
import pytz
from datetime import datetime

from odoo import http, fields, _
from odoo.http import content_disposition, request, Response
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.tools.misc import xlsxwriter
from odoo.addons.payment_jetcheckout_system.controllers.main import JetcheckoutSystemController as JetController


class PaymentSyncopsController(JetController):

    def _jetcheckout_connector_auth(self, company, header):
        code = header.split(' ', 1)[1]
        auth = base64.b64decode(code).decode('utf-8')
        username, password = auth.split(':', 1)
        connector = request.env['syncops.connector'].sudo().search([
            ('company_id', '=', company.id),
            ('active', '=', True),
            ('connected', '=', True),
            ('username', '=', username),
            ('token', '=', password),
        ], limit=1)
        return connector
    
    def _jetcheckout_prepare_syncops_transactions(self, tx, tz=None):
        tz = tz or pytz.timezone('Europe/Istanbul')
        offset = tz.utcoffset(fields.Datetime.now())
        branch = tx.acquirer_id._get_branch_line(name=tx.jetcheckout_vpos_name, user=tx.create_uid)
        values = {
            'id': tx.id,
            'ref': tx.jetcheckout_order_id,
            'state': tx.state,
            'partner_ref': tx.partner_id.ref or '',
            'partner_name': tx.partner_id.name or '',
            'card_6': tx.jetcheckout_card_number[:6] if tx.jetcheckout_card_number else '',
            'card_4': tx.jetcheckout_card_number[-4:] if tx.jetcheckout_card_number else '',
            'vpos_id': tx.jetcheckout_vpos_id or 0,
            'bank_payment_day': 1,
            'installment_count': tx.jetcheckout_installment_count,
            'installment_code': tx.jetcheckout_campaign_name or '',
            'payment_date': (tx.create_date + offset).strftime('%Y-%m-%d'),
            'payment_time': (tx.create_date + offset).strftime('%H:%M:%S'),
            'currency_code': tx.currency_id.name or '',
            'payment_amount': tx.amount,
            'payment_net_amount': tx.jetcheckout_payment_amount,
            'plus_installment': tx.jetcheckout_installment_plus,
            'payment_deferral': 0,
            'bank_id': 0,
            'bank_name': '',
            'refund_payment_id': '',
            'refund_currency_code': '',
            'refund_date': '',
            'refund_time': '',
            'branch_code': branch and branch.account_code or '',
            'company_code': tx.company_id.partner_id.ref or '',
            'payment_ref': '03',
        }
        if tx.source_transaction_id:
            values.update({
                'refund_payment_id': tx.source_transaction_id.id,
                'refund_currency_code': tx.source_transaction_id.currency_id.name,
                'refund_date': (tx.source_transaction_id.create_date + offset).strftime('%Y-%m-%d'),
                'refund_time': (tx.source_transaction_id.create_date + offset).strftime('%H:%M:%S'),
            })
        return values
 
    def _jetcheckout_connector_get_partner_info(self, partner=None):
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
                'jetcheckout_connector_partner_ref': partner['ref'],
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

    @http.route(['/syncops/payment/transactions'], type='http', auth='public', methods=['GET'], csrf=False, sitemap=False, save_session=False, website=True)
    def jetcheckout_syncops_transactions(self, **data):
        headers = request.httprequest.headers
        if 'Authorization' not in headers:
            return Response('Access Denied', status=401)

        company = request.env.company
        connector = self._jetcheckout_connector_auth(company, headers['Authorization'])
        if not connector:
            return Response('Access Denied', status=401)

        response = []
        if data:
            now = fields.Datetime.now()
            date_start = datetime.strptime(data['payment_date_start'], DT) if 'payment_date_start' in data else now
            date_end = datetime.strptime(data['payment_date_end'], DT) if 'payment_date_end' in data else now
            tz = pytz.timezone('Europe/Istanbul')
            offset = tz.utcoffset(now)
            domain = [
                ('company_id', '=', company.id),
                ('create_date', '>=', date_start - offset),
                ('create_date', '<=', date_end - offset),
            ]
            if 'payment_type' in data:
                if data['payment_type'] == 'payment':
                    domain.extend([('state', '=', 'done'), ('source_transaction_id', '=', False)])
                elif data['payment_type'] == 'cancel':
                    domain.extend([('state', '=', 'cancel'), ('source_transaction_id', '=', False)])
                elif data['payment_type'] == 'refund':
                    domain.extend([('state', '=', 'done'), ('source_transaction_id', '!=', False)])
                else:
                    domain.extend([('state', 'in', ('done', 'cancel'))])
            else:
                domain.extend([('state', 'in', ('done', 'cancel'))])

            transactions = request.env['payment.transaction'].sudo().search(domain)
            for transaction in transactions:
                values = self._jetcheckout_prepare_syncops_transactions(transaction)
                response.append(values)

        headers = [('Content-Type', 'application/json; charset=utf-8'), ('Cache-Control', 'no-store')]
        return request.make_response(json.dumps(response), headers)

    @http.route(['/syncops/payment/transactions/xlsx'], type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def jetcheckout_syncops_transactions_xlsx(self, **data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        headers = {
            'id': 'PAYMENTID',
            'ref': 'REFERENCECODE',
            'partner_ref': 'CUST_ERP_CODE',
            'id': 'CUST_ERP_NAME',
            'card_6': 'CARD_6',
            'card_4': 'CARD_4',
            'vpos_id': 'VPOSID',
            'bank_payment_day': 'BANK_PAYMENT_DAY',
            'state': 'STATUS',
            'installment_count': 'PERIOD',
            'installment_code': 'PERIOD_CODE',
            'payment_date': 'PAYMENTDATE',
            'payment_time': 'PAYMENTTIME',
            'currency_code': 'CURRENCYCODE',
            'payment_amount': 'PROCCESSAMOUNT',
            'payment_net_amount': 'PROCCESSNETAMOUN',
            'plus_installment': 'PLUS_PERIOD',
            'payment_deferral': 'PAYMENT_DEFERRAL',
            'bank_id': 'BANKID',
            'bank_name': 'BANK_NAME',
            'branch_code': 'HKONT',
            'refund_payment_id': 'REV_PAYMENTID',
            'refund_currency_code': 'REV_CURRENCYCODE',
            'refund_date': 'REV_DATE',
            'refund_time': 'REV_TIME',
            'company_code': 'BRANCH_CODE',
            'payment_ref': 'SOURCEID',
        }
        for i, col in enumerate(headers.values()):
            worksheet.write(0, i, col)

        transactions = request.env['payment.transaction'].sudo().search([
            ('id', 'in', list(map(int, data[''].split(',')))),
            ('company_id', '=', request.env.user.company_ids.ids)
        ])
        row = 0
        for transaction in transactions:
            row += 1
            values = self._jetcheckout_prepare_syncops_transactions(transaction)
            for i, key in enumerate(headers.keys()):
                worksheet.write(row, i, values[key])
        workbook.close()

        xlsx = output.getvalue()
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition('Transactions.xlsx'))
        ]
        return request.make_response(xlsx, headers=headers)
