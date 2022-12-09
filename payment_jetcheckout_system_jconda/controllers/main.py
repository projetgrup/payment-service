# -*- coding: utf-8 -*-
import werkzeug

from odoo import http, _
from odoo.http import request
from odoo.addons.payment_jetcheckout_system.controllers.main import JetcheckoutSystemController as JetController


class JetcheckoutSystemJcondaController(JetController):

    def _jetcheckout_connector_get_partner_balance(self, vat=None, company=None):
        balance = []
        result = request.env['jconda.connector'].sudo()._execute('payment_get_partner_balance', params={
            'company_id': 1,
            'vat': vat
        }, company=company)
        if result:
            for res in result:
                balance.append({
                    'amount': res['amount'],
                    'currency': request.env['res.currency'].sudo().with_context(active_test=False).search([('name', '=', res['currency_name'])], limit=1)
                })
        return balance

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
        values['balances'] = self._jetcheckout_connector_get_partner_balance(vat=values['partner'].vat, company=company)
        values['show_balance'] = bool(values['balances'])
        values['show_ledger'] = request.env['jconda.connector'].sudo()._count('payment_get_partner_ledger', company=company)
        values['show_partners'] = request.env['jconda.connector'].sudo()._count('payment_get_partner_list', company=company)
        values['partner_related'] = '__jetcheckout_partner_related' in request.session and request.session['__jetcheckout_partner_related']
        return values

    @http.route(['/my/payment/ledger', '/my/payment/ledger/page/<int:page>'], type='http', auth='user', website=True)
    def jetcheckout_portal_payment_page_ledger(self, page=0, step=10, **kwargs):
        values = self._jetcheckout_get_data()
        currencies = {}
        total = 0
        result = request.env['jconda.connector'].sudo()._execute('payment_get_partner_ledger', params={
            'company_id': 1,
            'vat': values['partner_related']['vat'] if values['partner_related'] else values['partner'].vat
        }, company=values['company'])
        if result == None:
            raise werkzeug.exceptions.NotFound()

        for res in result:
            currency = res['currency_name']
            lines = [{
                'date': res['date'],
                'due_date': res['due_date'],
                'type': res['type'],
                'name': res['name'],
                'description': res['description'],
                'currency': request.env['res.currency'].sudo().with_context(active_test=False).search([('name', '=', res['currency_name'])], limit=1),
                'amount': res['amount'],
                'balance': res['balance'],
            }]
            if currency in currencies:
                currencies[currency].extend(lines)
            else:
                currencies[currency] = lines
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
        result = request.env['jconda.connector'].sudo()._execute('payment_get_partner_list', params={})
        if not result == None:
            return result
        return False

    @http.route(['/my/payment/partners/select'], type='json', auth='user', website=True)
    def jetcheckout_portal_payment_page_partners_select(self, **kwargs):
        request.session['__jetcheckout_partner_related'] = {
            'name': kwargs.get('company'),
            'vat': kwargs.get('vat'),
        }
        return {
            'render': request.env['ir.ui.view']._render_template('payment_jetcheckout_system_jconda.payment_partner_balance', {
                'balances': self._jetcheckout_connector_get_partner_balance(kwargs.get('vat'))
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
                'balances': self._jetcheckout_connector_get_partner_balance(partner.vat)
            })
        }
