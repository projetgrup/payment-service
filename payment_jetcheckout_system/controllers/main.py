# -*- coding: utf-8 -*-
import werkzeug
import base64
from urllib.parse import urlparse

from odoo import http, _
from odoo.http import request
from odoo.tools import html_escape
from odoo.tools.misc import get_lang
from odoo.exceptions import AccessError
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


class JetcheckoutSystemController(JetController):

    def _jetcheckout_check_redirect(self, partner):
        company_id = partner.company_id.id or request.env.company.id
        if not request.website.company_id.id == company_id:
            website = request.env['website'].sudo().search([('company_id', '=', company_id)], limit=1)
            if website:
                path = urlparse(request.httprequest.url).path
                return werkzeug.utils.redirect(website.domain + path)
            else:
                raise werkzeug.exceptions.NotFound()
        return False

    def _jetcheckout_get_parent(self, token):
        id, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not id or not token:
            raise werkzeug.exceptions.NotFound()

        partner = request.env['res.partner'].sudo().search([('id', '=', id), ('access_token', '=', token)], limit=1)
        if not partner:
            raise werkzeug.exceptions.NotFound()

        return partner

    def _jetcheckout_check_user(self):
        path = urlparse(request.httprequest.referrer).path
        if '/my/payment' in path and not request.env.user.active:
            raise AccessError(_('Access Denied'))
        return super()._jetcheckout_check_user()

    def _jetcheckout_tx_vals(self, **kwargs):
        vals = super()._jetcheckout_tx_vals(**kwargs)
        ids = kwargs.get('payment_ids', [])
        if ids:
            vals.update({'jetcheckout_item_ids': [(6, 0, ids)]})
        if request.env.company.system:
            vals.update({'jetcheckout_payment_ok': False})
        return vals

    def _jetcheckout_process(self, **kwargs):
        url, tx, status = super()._jetcheckout_process(**kwargs)
        if not status and tx.company_id.system:
            status = True
            url = '%s?=%s' % (tx.partner_id._get_share_url(), kwargs.get('order_id'))
        return url, tx, status

    def _jetcheckout_system_page_values(self, company, system, partner, transaction):
        currency = company.currency_id
        lang = get_lang(request.env)
        acquirer = self._jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        campaign = transaction.jetcheckout_campaign_name if transaction else partner.campaign_id.name if partner else ''
        card_family = self._jetcheckout_get_card_family(acquirer=acquirer, campaign=campaign)
        token = partner._get_token()
        return {
            'partner': partner,
            'company': company,
            'website': request.website,
            'footer': request.website.payment_footer,
            'acquirer': acquirer,
            'campaign': {
                'name': campaign,
                'visible': False,
            },
            'card_family': card_family,
            'success_url': '/payment/card/success',
            'fail_url': '/payment/card/fail',
            'tx': transaction,
            'system': system,
            'token': token,
            'no_terms': not acquirer.provider == 'jetcheckout' or acquirer.jetcheckout_no_terms,
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

    @http.route('/p/<token>', type='http', auth='public', methods=['GET'], csrf=False, sitemap=False, website=True)
    def jetcheckout_system_payment_page(self, token, **kwargs):
        partner = self._jetcheckout_get_parent(token)
        transaction = None
        if '' in kwargs:
            transaction = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id','=',kwargs[''])], limit=1)
            if not transaction:
                raise werkzeug.exceptions.NotFound()

        company = partner.company_id or request.website.company_id or request.env.company
        if not company == request.env.company:
            raise werkzeug.exceptions.NotFound()
        system = company.system or partner.system or 'jetcheckout_system'
        values = self._jetcheckout_system_page_values(company, system, partner, transaction)
        return request.render('payment_%s.payment_page' % system, values)

    @http.route('/p/<token>/<int:pid>', type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, website=True)
    def jetcheckout_system_payment_page_file(self, token, pid, **kwargs):
        partner = self._jetcheckout_get_parent(token)
        payment = request.env['payment.item'].sudo().browse(pid)
        if not payment.parent_id.id == partner.id or payment.paid:
            raise werkzeug.exceptions.NotFound()

        pdf = payment.file
        if not pdf:
            raise werkzeug.exceptions.NotFound()

        pdf = base64.b64decode(pdf)
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'attachment; filename="%s.pdf"' % html_escape(payment.description)),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

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

    @http.route('/my/payment', type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def jetcheckout_portal_payment_page(self, **kwargs):
        if '_tx_partner' in request.session:
            partner = request.env['res.partner'].browse(request.session['_tx_partner'])
        else:
            partner = request.env.user.partner_id

        redirect = self._jetcheckout_check_redirect(partner)
        if redirect:
            return redirect

        values = self._jetcheckout_get_data()
        values.update({
            'fail_url': '/my/payment/success',
            'success_url': '/my/payment/fail',
            'show_reset': True,
        })

        # remove hash if exists
        # it could be there because of api module
        if '__tx_hash' in request.session:
            del request.session['__tx_hash']

        return request.render('payment_jetcheckout_system.payment_page', values)

    @http.route(['/my/payment/success', '/my/payment/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_portal_return(self, **kwargs):
        kwargs['result_url'] = '/my/payment/result'
        self._jetcheckout_process(**kwargs)
        return werkzeug.utils.redirect(kwargs['result_url'])

    @http.route('/my/payment/result', type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def jetcheckout_portal_payment_page_result(self, **kwargs):
        values = self._jetcheckout_get_data()
        last_tx_id = request.session.get('__tx_id')
        values['tx'] = request.env['payment.transaction'].sudo().browse(last_tx_id)
        if last_tx_id:
            del request.session['__tx_id']
        return request.render('payment_jetcheckout_system.payment_page_result', values)

    @http.route(['/my/payment/transactions', '/my/payment/transactions/page/<int:page>'], type='http', auth='user', website=True)
    def jetcheckout_portal_payment_page_transactions(self, page=0, tpp=20, **kwargs):
        values = self._jetcheckout_get_data()
        tx_ids = request.env['payment.transaction'].sudo().search([
            ('acquirer_id', '=', values['acquirer'].id),
            ('partner_id', '=', values['partner'].id)
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

    @http.route('/my/payment/<token>', type='http', auth='public', methods=['GET'], sitemap=False, website=True)
    def jetcheckout_portal_payment_page_signin(self, token, **kwargs):
        partner = self._jetcheckout_get_parent(token)
        redirect = self._jetcheckout_check_redirect(partner)
        if redirect:
            return redirect

        if partner.is_portal:
            if request.env.user.has_group('base.group_user'):
                request.session['_tx_partner'] = partner.id
                return werkzeug.utils.redirect('/my/payment')
            else:
                user = partner.users_id
                request.session.authenticate(request.db, user.login, {'token': token})
                return werkzeug.utils.redirect('/my/payment')
        else:
            return werkzeug.utils.redirect('/p/%s' % token)
