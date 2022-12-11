# -*- coding: utf-8 -*-
import werkzeug

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.payment_jetcheckout_system.controllers.main import JetcheckoutSystemController as JetController


class JetcheckoutSystemJcondaController(JetController):

    def _jetcheckout_connector_get_partner_balance(self, vat, ref, company=None):
        balances = []
        company = company or request.env.company
        company_id = company.sudo().partner_id.ref
        result = request.env['jconda.connector'].sudo()._execute('payment_get_partner_balance', params={
            'company_id': company_id,
            'vat': vat,
            'ref': vat,
            #'ref': ref, TODO will be soon asap
        }, company=company)
        if result:
            for res in result:
                currency_name = res['currency_name']

                # Following two lines are for compatibility purposes
                if currency_name == 'TRL':
                    currency_name = 'TRY'

                currency = request.env['res.currency'].sudo().with_context(active_test=False).search([('name', '=', currency_name)], limit=1)
                if not currency:
                    continue

                balances.append({'amount': res['amount'], 'currency': currency})
        return balances

    def _jetcheckout_connector_can_show_partner_ledger(self, company=None):
        company = company or request.env.company
        return request.env['jconda.connector'].sudo()._count('payment_get_partner_ledger', company=company)

    def _jetcheckout_connector_can_show_partner_balance(self, balance):
        return bool(balance)

    def _jetcheckout_connector_can_access_partner_list(self, company=None):
        user = request.env.user.sudo()
        company = company or request.env.company
        return not user.share and company.id in user.company_ids.ids and request.env['jconda.connector'].sudo()._count('payment_get_partner_list', company=company)

    def _jetcheckout_tx_vals(self, **kwargs):
        vals = super()._jetcheckout_tx_vals(**kwargs)
        if '__jetcheckout_partner_related' in request.session:
            partner_related = request.session['__jetcheckout_partner_related']
            vals.update({
                'jetcheckout_connector_partner_name': partner_related['name'],
                'jetcheckout_connector_partner_vat': partner_related['vat'],
            })
        return vals

    def _jetcheckout_get_data(self, acquirer=False, company=False, transaction=False, balance=True):
        values = super()._jetcheckout_get_data(acquirer=acquirer, company=company, transaction=transaction, balance=balance)

        if '__jetcheckout_partner_related' in request.session:
            partner_related = request.session['__jetcheckout_partner_related']
            vat = partner_related['vat']
            ref = partner_related['ref']
        else:
            vat = values['partner'].vat
            ref = values['partner'].ref

        values['balances'] = self._jetcheckout_connector_get_partner_balance(vat, ref, company)
        values['show_balance'] = self._jetcheckout_connector_can_show_partner_balance(values['balances'])
        values['show_ledger'] = self._jetcheckout_connector_can_show_partner_ledger(company)
        values['show_partners'] = self._jetcheckout_connector_can_access_partner_list(company)
        values['partner_related'] = request.session.get('__jetcheckout_partner_related', {})
        return values

    @http.route(['/my/payment/ledger', '/my/payment/ledger/page/<int:page>'], type='http', auth='user', website=True)
    def jetcheckout_portal_payment_page_ledger(self, page=0, step=10, **kwargs):
        values = self._jetcheckout_get_data()
        currencies = {}
        total = 0
        year = fields.Date.today().year
        date_start = '%s-01-01 00:00:00' % year
        date_end = '%s-12-31 23:59:59' % year
        result = request.env['jconda.connector'].sudo()._execute('payment_get_partner_ledger', params={
            'company_id': values['company'].sudo().partner_id.ref,
            'vat': values['partner_related']['vat'] if values['partner_related'] else values['partner'].vat,
            'ref': values['partner_related']['vat'] if values['partner_related'] else values['partner'].vat,
            #'ref': values['partner_related']['ref'] if values['partner_related'] else values['partner'].ref, TODO will be soon asap
            'date_start': date_start,
            'date_end': date_end,
        }, company=values['company'])
        if result == None:
            raise werkzeug.exceptions.NotFound()

        for res in result:
            currency_name = res['currency_name']
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
                'currency': currency,
            }]
            if currency_name in currencies:
                currencies[currency_name].extend(lines)
            else:
                currencies[currency_name] = lines
            total += 1

        pager = request.website.pager(url='/my/payment/ledger', total=total, page=page, step=step, scope=7, url_args=kwargs)
        #offset = pager['offset']
        #lines = lines[offset: offset + step]
        values.update({
            'pager': pager,
            'currencies': currencies,
            'step': step
        })
        return request.render('payment_jetcheckout_system_jconda.payment_page_ledger', values)

    @http.route(['/my/payment/partners'], type='json', auth='user', website=True)
    def jetcheckout_portal_payment_page_partners(self, **kwargs):
        if not self._jetcheckout_connector_can_access_partner_list():
            return []

        result = request.env['jconda.connector'].sudo()._execute('payment_get_partner_list', params={
            'company_id': request.env.company.sudo().partner_id.ref,
        })
        if not result == None:
            return result
        return []

    @http.route(['/my/payment/partners/select'], type='json', auth='user', website=True)
    def jetcheckout_portal_payment_page_partners_select(self, **kwargs):
        if not self._jetcheckout_connector_can_access_partner_list():
            return False

        request.session['__jetcheckout_partner_related'] = {
            'name': kwargs.get('company'),
            'vat': kwargs.get('vat'),
            'ref': kwargs.get('ref'),
        }

        balances = self._jetcheckout_connector_get_partner_balance(kwargs.get('vat'), kwargs.get('ref'))
        return {
            'render': request.env['ir.ui.view']._render_template('payment_jetcheckout_system_jconda.payment_partner_balance', {
                'balances': balances,
                'show_balance': self._jetcheckout_connector_can_show_partner_balance(balances),
                'show_ledger': self._jetcheckout_connector_can_show_partner_ledger(),
            })
        }

    @http.route(['/my/payment/partners/reset'], type='json', auth='user', website=True)
    def jetcheckout_portal_payment_page_partners_reset(self, **kwargs):
        if '__jetcheckout_partner_related' not in request.session:
            return False

        del request.session['__jetcheckout_partner_related']
        partner = request.env.user.partner_id
        return {
            'name': partner.name,
            'render': request.env['ir.ui.view']._render_template('payment_jetcheckout_system_jconda.payment_partner_balance', {
                'balances': self._jetcheckout_connector_get_partner_balance(vat=partner.vat, ref=partner.ref)
            })
        }
