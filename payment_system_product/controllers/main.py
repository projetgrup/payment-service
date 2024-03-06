# -*- coding: utf-8 -*-
import werkzeug
from urllib.parse import urlparse

from .sse import dispatch
from odoo import _
from odoo.http import route, request, Response, Controller
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as SystemController


class PaymentProductController(Controller):

    @route(['/longpolling/prices'], type='http', methods=['GET'], auth='public', cors='*')
    def payment_product_price(self, **kwargs):
        return Response(dispatch.poll(request.db, request.env.company.id, request.uid, request.context), headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        })


class PaymentSystemProductController(SystemController):

    def _check_product_page(self, **kwargs):
        if not request.env.company.system_product:
            raise werkzeug.exceptions.NotFound()

        if request.env.user.share and not 'id' in kwargs:
            raise werkzeug.exceptions.NotFound()

    def _redirect_product_page(self, website_id=None, company_id=None):
        website = False
        websites = request.env['website'].sudo()
        if website_id:
            website = websites.browse(website_id)
        elif company_id:
            website = websites.search([
                ('domain', '=', request.website.domain),
                ('company_id', '=', company_id)
            ], limit=1)

        if not website:
            raise werkzeug.exceptions.NotFound()

        website._force()
        path = request.httprequest.path
        query = request.httprequest.query_string
        if query:
            path += '?' + query.decode('utf-8')
        return werkzeug.utils.redirect(path)

    @route('/my/product', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def _check_product_page(self, **kwargs):
        self._check_advance_page(**kwargs)
        w_id = request.website.id
        website_id = int(kwargs.get('id', w_id))
        if w_id != website_id:
            return self._redirect_product_page(website_id=website_id)

        company = request.env.company
        user = request.env.user
        companies = user.company_ids
        if len(companies) == 1 and request.website.company_id.id != user.company_id.id:
            return self._redirect_product_page(company_id=user.company_id.id)

        if company.id != request.website.company_id.id:
            return self._redirect_product_page(company_id=company.id)

        self._del()

        partner = user.partner_id if user.has_group('base.group_portal') else request.website.user_id.partner_id.sudo()
        values = self._prepare(partner=partner, company=company)
        companies = values['companies']
        if user.share:
            companies = []
        else:
            companies = companies.filtered(lambda x: x.system_product and x.id in user.company_ids.ids)

        products = request.env['product.template'].sudo().search([
            ('company_id', '=', company.id),
            ('system', '=', company.system),
            ('payment_page_ok', '=', True),
        ])    
        values.update({
            'success_url': '/my/payment/success',
            'fail_url': '/my/payment/fail',
            'companies': companies,
            'system': company.system,
            'subsystem': company.subsystem,
            'vat': kwargs.get('vat'),
            'flow': 'dynamic',
            'products': products,
            'readonly': True,
        })

        if 'values' in kwargs and isinstance(kwargs['values'], dict):
            values.update({**kwargs['values']})

        return request.render('payment_jetcheckout_system.page_payment', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })


    def _prepare_system(self,  company, system, partner, transaction, options={}):
        res = super()._prepare_system(company, system, partner, transaction, options=options)
        if company.system_product:
            categs = request.env['product.category'].sudo().with_context(system=system).search([
                ('system', '!=', False),
                ('company_id', '=', company.id),
            ])
            products = request.env['product.template'].sudo().with_context(system=system).search([
                ('system', '!=', False),
                ('payment_page_ok', '=', True),
                ('company_id', '=', company.id),
            ])

            try:
                installment = self._prepare_installment()
                commission = installment['rows'][0]['installments'][0]['crate']
            except:
                commission = 0.0

            res.update({
                'categs': categs,
                'products': products,
                'commission': commission / 100,
                'validity': company.system_product_payment_validity_ok and company.system_product_payment_validity_time or 0,
                'margin': 1,
            })
        return res

    @route('/my/product/policy', type='json', auth='public', website=True)
    def page_product_policy(self):
        token = urlparse(request.httprequest.referrer).path.rsplit('/', 1).pop()
        pid, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not pid or not token:
            raise

        company = request.env.company
        partner = request.env['res.partner'].sudo().search([
            ('id', '=', pid),
            ('access_token', '=', token),
            ('company_id', '=', company.id),
        ], limit=1)
        if not partner:
            raise

        return {
            'name': partner.name,
            'vat': partner.vat,
            'address': partner.street,
            'state': partner.state_id.name,
            'country': partner.country_id.name,
            'phone': partner.mobile or partner.phone,
            'website': partner.website,
        }

    @route('/my/product/policy/send', type='json', auth='public', website=True)
    def page_product_policy_send(self):
        token = urlparse(request.httprequest.referrer).path.rsplit('/', 1).pop()
        pid, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not pid or not token:
            raise

        company = request.env.company
        partner = request.env['res.partner'].sudo().search([
            ('id', '=', pid),
            ('access_token', '=', token),
            ('company_id', '=', company.id),
        ], limit=1)
        if not partner:
            raise

        if not partner.email:
            return {'error': _('Please specify an email address before proceeding.')}
        
        template = request.env.ref('payment_product.mail_policy')
        mail_server = company.mail_server_id

        context = request.env.context.copy()
        context.update({
            'company': company,
            'partner': partner,
            'tz': partner.tz,
            'lang': partner.lang,
            'server': mail_server,
            'from': mail_server.email_formatted or company.email_formatted,
        })
        template.with_context(context).send_mail(partner.id, force_send=True, email_values={
            'is_notification': True,
            'mail_server_id': mail_server.id,
        })

        return {}
