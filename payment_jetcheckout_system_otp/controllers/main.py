# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


class JetcheckoutSystemOtpController(JetController):

    @http.route('/otp', type='http', auth='public', methods=['GET'], sitemap=False, website=True)
    def jetcheckout_system_otp_login_page(self, **kwargs):
        company = request.env.company
        system = company.system
        acquirer = self._jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        values = {
            'company': company,
            'website': request.website,
            'footer': request.website.payment_footer,
            'acquirer': acquirer,
            'system': system,
        }
        return request.render('payment_jetcheckout_system_otp.otp_login_page', values)

    @http.route(['/otp/prepare'], type='json', auth='public', sitemap=False, website=True)
    def jetcheckout_system_otp_login_prepare(self, **kwargs):
        partner = request.env['res.partner'].sudo().search([('company_id', '=', request.env.company.id), '|', '|', '|', ('email', 'like', '%%%s%%' % kwargs['login']), ('vat', 'like', '%%%s%%' % kwargs['login']), ('phone', 'like', '%%%s%%' % kwargs['login']), ('mobile', 'like', '%%%s%%' % kwargs['login'])], limit=1)
        if partner:
            otp = request.env['res.partner.otp'].sudo().create({
                'partner_id': partner.id,
                'company_id': partner.company_id.id,
                'lang': partner.lang,
            })
            return otp.id
        return 0

    @http.route(['/otp/validate'], type='json', auth='public', sitemap=False, website=True)
    def jetcheckout_system_otp_login_validate(self, **kwargs):
        otp = request.env['res.partner.otp'].sudo().search([('company_id', '=', request.env.company.id), ('id', '=', kwargs['id']), ('partner_id', '!=', False), ('code', '=', kwargs['code']), ('date', '>', fields.Datetime.now())], limit=1)
        if otp:
            return {
                'url': otp.partner_id._get_payment_url()
            }
        else:
            return {
                'error': _('Authentication code is not correct. Please check and retype.')
            }
