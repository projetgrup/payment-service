# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, _
from odoo.http import request
from odoo.tools.misc import get_lang
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


class JetcheckoutSystemController(JetController):

    def _jetcheckout_get_parent(self, token):
        id, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not id or not token:
            raise werkzeug.exceptions.NotFound()

        partner = request.env['res.partner'].sudo().search([('id', '=', id), ('access_token', '=', token)], limit=1)
        if not partner:
            raise werkzeug.exceptions.NotFound()

        return partner

    def _jetcheckout_tx_vals(self, **kwargs):
        vals = super()._jetcheckout_tx_vals(**kwargs)
        ids = kwargs.get('payment_ids',[])
        if ids:
            vals.update({'jetcheckout_item_ids': [(6, 0, ids)]})
        return vals

    def _jetcheckout_process(self, **kwargs):
        url, tx = super()._jetcheckout_process(**kwargs)
        if tx.company_id.system:
            url = '%s?=%s' % (tx.partner_id._get_share_url(), kwargs.get('order_id'))
        return url, tx

    def _jetcheckout_system_page_values(self, company, system, parent, transaction):
        currency = company.currency_id
        lang = get_lang(request.env)
        acquirer = self._jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        card_family = self._jetcheckout_get_card_family(acquirer)
        return {
            'parent': parent,
            'company': company,
            'website': request.website,
            'footer': request.website.payment_footer,
            'acquirer': acquirer,
            'card_family': card_family,
            'footer': '',
            'success_url': '/payment/card/success',
            'fail_url': '/payment/card/fail',
            'tx': transaction,
            'system': system,
            'currency': {
                'self' : currency,
                'id' : currency.id,
                'name' : currency.name,
                'decimal' : currency.decimal_places,
                'symbol' : currency.symbol,
                'position' : currency.position,
                'separator' : lang.decimal_point,
                'thousand' : lang.thousands_sep,
            },
        }

    @http.route('/p/<int:parent_id>/<string:access_token>', type='http', auth='public', methods=['GET'], csrf=False, sitemap=False, website=True)
    def jetcheckout_system_payment_page_legacy(self, parent_id, access_token, **kwargs):
        parent = request.env['res.partner'].sudo().browse(parent_id)
        if not parent or not parent.access_token == access_token:
            raise werkzeug.exceptions.NotFound()
        token = parent._get_token()
        return self.jetcheckout_system_payment_page(token)

    @http.route('/p/<token>', type='http', auth='public', methods=['GET'], csrf=False, sitemap=False, website=True)
    def jetcheckout_system_payment_page(self, token, **kwargs):
        parent = self._jetcheckout_get_parent(token)
        transaction = None
        if '' in kwargs:
            transaction = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id','=',kwargs[''])], limit=1)
            if not transaction:
                raise werkzeug.exceptions.NotFound()

        company = parent.company_id
        if company and not company == request.env.company:
            raise werkzeug.exceptions.NotFound()
        system = company.system
        values = self._jetcheckout_system_page_values(company, system, parent, transaction)
        return request.render('payment_%s.payment_page' % system, values)

    @http.route(['/p/privacy'], type='json', auth='public', website=True, csrf=False)
    def jetcheckout_privacy_policy(self):
        return request.website.payment_privacy_policy

    @http.route(['/p/agreement'], type='json', auth='public', website=True, csrf=False)
    def jetcheckout_sale_agreement(self):
        return request.website.payment_sale_agreement

    @http.route(['/p/membership'], type='json', auth='public', website=True, csrf=False)
    def jetcheckout_membership_agreement(self):
        return request.website.payment_membership_agreement

    @http.route(['/p/contact'], type='json', auth='public', website=True, csrf=False)
    def jetcheckout_contact_page(self):
        return request.website.payment_contact_page

    @http.route('/my/payment/<token>', type='http', auth='public', methods=['GET'], sitemap=False, website=True)
    def jetcheckout_portal_payment_page_signin(self, token, **kwargs):
        parent = self._jetcheckout_get_parent(token)
        user = parent.users_id
        request.session.authenticate(request.db, user.login, {'token': token})
        return werkzeug.utils.redirect('/my/payment')

    @http.route('/my/payment', type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def jetcheckout_portal_payment_page(self, **kwargs):
        values = self._jetcheckout_get_data()
        values['success_url'] = '/my/payment/success'
        values['fail_url'] = '/my/payment/fail'

        try:
            db_source = request.env['ir.database.external'].sudo().search([('company_id', '=', values['company'].id)], limit=1)
            result = db_source._get('partner_balance', values['partner'])
            values['balance'] = result['amount']
            values['balance_currency'] = request.env['res.currency'].sudo().search([('name', '=', result['currency'])], limit=1)
            values['show_balance'] = True
        except:
            values['show_balance'] = False

        # remove hash if exists
        # it could be there because of api module
        if 'hash' in request.session:
            del request.session['hash']

        return request.render('payment_jetcheckout_system.payment_page', values)

    @http.route(['/my/payment/success', '/my/payment/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_portal_return(self, **kwargs):
        kwargs['result_url'] = '/my/payment/result'
        self._jetcheckout_process(**kwargs)
        return werkzeug.utils.redirect(kwargs['result_url'])

    @http.route('/my/payment/result', type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def jetcheckout_portal_payment_page_result(self, **kwargs):
        values = self._jetcheckout_get_data()
        last_tx_id = request.session.get('__jetcheckout_last_tx_id')
        values['tx'] = request.env['payment.transaction'].sudo().browse(last_tx_id)
        if last_tx_id:
            del request.session['__jetcheckout_last_tx_id']
        return request.render('payment_jetcheckout_system.payment_page_result', values)

    @http.route(['/my/payment/transactions', '/my/payment/transactions/page/<int:page>'], type='http', auth='user', website=True)
    def jetcheckout_portal_payment_page_transactions(self, page=0, tpp=20, **kwargs):
        values = self._jetcheckout_get_data()
        tx_ids = request.env['payment.transaction'].sudo().search([
            ('acquirer_id', '=', values['acquirer'].id),
            ('partner_id', 'in', (values['partner_id'], values['contact_id']))
        ])
        pager = request.website.pager(url='/my/payment/transactions', total=len(tx_ids), page=page, step=tpp, scope=7, url_args=kwargs)
        offset = pager['offset']
        txs = tx_ids[offset: offset + tpp]
        values.update({
            'pager': pager,
            'txs': txs,
            'tpp': tpp,
        })
        return request.render('payment_jetcheckout_system.payment_page_transaction', values)
