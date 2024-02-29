# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from werkzeug.exceptions import NotFound

from odoo import _
from odoo.http import route, request
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller


class CustomerPortal(portal.CustomerPortal):
    @route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'jewelry':
            return request.redirect('/my/payment')
        return super().home(**kwargs)


class PayloxSystemJewelryController(Controller):

#    @route(['/my/jewelry'], type='http', auth='user', website=True)
#    def page_jewelry(self, **kwargs):
#        system = kwargs.get('system', request.env.company.system)
#        if system == 'jewelry':
#            return request.redirect('/my/payment')
#        return super().home(**kwargs)
#
#    def _get_tx_vals(self, **kwargs):
#        res = super()._get_tx_vals(**kwargs)
#        system = kwargs.get('system', request.env.company.system)
#        if system == 'jewelry':
#            pass
#        return res

    def _prepare_system(self,  company, system, partner, transaction, options={}):
        res = super()._prepare_system(company, system, partner, transaction, options=options)
        if system == 'jewelry':
            products = request.env['product.template'].sudo().with_context(system=system).search([
                ('system', '=', 'jewelry'),
                ('payment_page_ok', '=', True),
                ('company_id', '=', request.env.company.id),
            ])

            try:
                installment = self._prepare_installment()
                commission = installment['rows'][0]['installments'][0]['crate']
            except:
                commission = 0.0

            res.update({
                'products': products,
                'commission': commission / 100,
                'validity': company.jewelry_payment_validity_ok and company.jewelry_payment_validity_time or 0,
                'margin': 1 + (partner.system_jewelry_price_margin / 100),
            })
        return res

    @route('/my/jewelry/policy', type='json', auth='public', website=True)
    def page_jewelry_policy(self):
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

    @route('/my/jewelry/policy/send', type='json', auth='public', website=True)
    def page_jewelry_policy_send(self):
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
        
        template = request.env.ref('payment_jewelry.mail_policy')
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

    @route(['/my/jewelry/register'], type='http', auth='public', website=True)
    def page_jewelry_register(self, **kwargs):
        system = request.env.company.system
        if system == 'jewelry':
            values = {
                'company': request.env.company,
            }
            return request.render('payment_jewelry.page_regsiter', values)
        raise NotFound()

    @route('/my/jewelry/register/query', type='json', auth='public', website=True)
    def page_jewelry_register_query(self, vat):
        result = request.env['syncops.connector'].sudo()._execute('partner_get_company', params={'vat': vat})
        if result is None:
            return {'error': _('An error occured. Please contact with system administrator.')}
        return result[0]
