# -*- coding: utf-8 -*-
import werkzeug
import base64
import re
from urllib.parse import urlparse

from odoo import http, _
from odoo.http import request
from odoo.tools import html_escape
from odoo.exceptions import AccessError
from odoo.addons.payment_jetcheckout.controllers.main import PayloxController as Controller


class PayloxSystemController(Controller):

    def _check_redirect(self, partner):
        company_id = partner.company_id.id or request.env.company.id
        if not request.website.company_id.id == company_id:
            website = request.env['website'].sudo().search([('company_id', '=', company_id)], limit=1)
            if website:
                path = urlparse(request.httprequest.url).path
                return werkzeug.utils.redirect(website.domain + path)
            else:
                raise werkzeug.exceptions.NotFound()
        return False

    def _get_parent(self, token):
        id, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not id or not token:
            raise werkzeug.exceptions.NotFound()

        partner = request.env['res.partner'].sudo().search([('id', '=', id), ('access_token', '=', token)], limit=1)
        if not partner:
            raise werkzeug.exceptions.NotFound()

        return partner

    def _check_user(self):
        path = urlparse(request.httprequest.referrer).path
        if '/my/payment' in path and not request.env.user.active:
            raise AccessError(_('Access Denied'))
        return super()._check_user()

    def _get_tx_vals(self, **kwargs):
        vals = super()._get_tx_vals(**kwargs)
        ids = kwargs.get('payments', [])
        if ids:
            vals.update({'jetcheckout_item_ids': [(6, 0, ids)]})
        if request.env.company.system:
            vals.update({'jetcheckout_payment_ok': False})
        return vals

    def _process(self, **kwargs):
        url, tx, status = super()._process(**kwargs)
        if not status and (tx.company_id.system or tx.partner_id.system):
            status = True
            url = '%s?=%s' % (tx.partner_id._get_share_url(), kwargs.get('order_id'))
        return url, tx, status

    def _prepare_system(self, company, system, partner, transaction):
        currency = company.currency_id
        acquirer = self._get_acquirer()
        type = self._get_type()
        campaign = transaction.jetcheckout_campaign_name if transaction else partner.campaign_id.name if partner else ''
        card_family = self._get_card_family(acquirer=acquirer, campaign=campaign)
        token = partner._get_token()
        return {
            'ok': True,
            'partner': partner,
            'partner_name': partner.name,
            'company': company,
            'website': request.website,
            'footer': request.website.payment_footer,
            'user': not request.env.user.share,
            'acquirer': acquirer,
            'campaign': campaign,
            'card_family': card_family,
            'success_url': '/payment/card/success',
            'fail_url': '/payment/card/fail',
            'tx': transaction,
            'system': system,
            'token': token,
            'type': type,
            'currency': currency,
            'no_terms': not acquirer.provider == 'jetcheckout' or acquirer.jetcheckout_no_terms,
        }

    @http.route('/p/<token>', type='http', auth='public', methods=['GET'], csrf=False, sitemap=False, website=True)
    def page_system_payment(self, token, **kwargs):
        partner = self._get_parent(token)
        transaction = None
        if '' in kwargs:
            txid = re.split(r'\?|%3F', kwargs[''])[0]
            transaction = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', txid)], limit=1)
            if not transaction:
                raise werkzeug.exceptions.NotFound()

        company = partner.company_id or request.website.company_id or request.env.company
        if not company == request.env.company:
            raise werkzeug.exceptions.NotFound()
        system = company.system or partner.system or 'jetcheckout_system'
        values = self._prepare_system(company, system, partner, transaction)
        return request.render('payment_%s.page_payment' % system, values)

    @http.route('/p/<token>/<int:pid>', type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, website=True)
    def page_system_payment_file(self, token, pid, **kwargs):
        partner = self._get_parent(token)
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
    def page_system_privacy_policy(self):
        return request.website.payment_privacy_policy

    @http.route(['/p/agreement'], type='json', auth='public', website=True, csrf=False)
    def page_system_sale_agreement(self):
        return request.website.payment_sale_agreement

    @http.route(['/p/membership'], type='json', auth='public', website=True, csrf=False)
    def page_system_membership_agreement(self):
        return request.website.payment_membership_agreement

    @http.route(['/p/contact'], type='json', auth='public', website=True, csrf=False)
    def page_system_contact_page(self):
        return request.website.payment_contact_page

    @http.route('/my/payment', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_system_portal(self, **kwargs):
        if request.env.user.has_group('base.group_public'):
            raise werkzeug.exceptions.NotFound()

        if request.httprequest.method == 'POST' and 'pid' in kwargs:
            partner = self._get_parent(kwargs['pid'])
        else:
            partner = request.env.user.partner_id

        redirect = self._check_redirect(partner)
        if redirect:
            return redirect

        values = self._prepare(partner=partner)
        values.update({
            'success_url': '/my/payment/success',
            'fail_url': '/my/payment/fail',
            'show_reset': True,
        })

        # remove hash if exists
        # it could be there because of api module
        self._del('hash')

        return request.render('payment_jetcheckout_system.page_payment', values)

    @http.route(['/my/payment/success', '/my/payment/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def page_system_portal_return(self, **kwargs):
        kwargs['result_url'] = '/my/payment/result'
        url, tx, status = self._process(**kwargs)
        if not status and tx.jetcheckout_order_id:
            url += '?=%s' % tx.jetcheckout_order_id
        return werkzeug.utils.redirect(url)

    @http.route('/my/payment/result', type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def page_system_result(self, **kwargs):
        values = self._prepare()
        if '' in kwargs:
            txid = re.split(r'\?|%3F', kwargs[''])[0]
            values['tx'] = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', txid)], limit=1)
        else:
            txid = self._get('tx', 0)
            values['tx'] = request.env['payment.transaction'].sudo().browse(txid)
        self._del()
        return request.render('payment_jetcheckout_system.page_result', values)

    @http.route(['/my/payment/transactions', '/my/payment/transactions/page/<int:page>'], type='http', auth='user', methods=['GET'], website=True)
    def page_system_transaction(self, page=0, tpp=20, **kwargs):
        values = self._prepare()
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
        return request.render('payment_jetcheckout_system.page_transaction', values)

    @http.route('/my/payment/<token>', type='http', auth='public', methods=['GET'], sitemap=False, website=True)
    def page_system_login(self, token, **kwargs):
        partner = self._get_parent(token)
        redirect = self._check_redirect(partner)
        if redirect:
            return redirect

        if partner.is_portal:
            if request.env.user.has_group('base.group_public'):
                user = partner.users_id
                request.session.authenticate(request.db, user.login, {'token': token})
            return request.render('payment_jetcheckout_system.page_login', {'token': token})
        else:
            return werkzeug.utils.redirect('/p/%s' % token)
