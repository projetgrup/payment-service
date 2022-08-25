# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.phone_validation.tools import phone_validation
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
        company = request.env.company
        country = company.country_id
        login = kwargs['login']
        number = phone_validation.phone_format(
            login,
            country.code if country else None,
            country.phone_code if country else None,
            force_format='INTERNATIONAL',
            raise_exception=False
        )
        partner = request.env['res.partner'].sudo().search([('company_id', '=', company.id), ('parent_id', '=', False), '|', '|', '|', ('email', '=ilike', login), ('child_ids.vat', 'like', '%%%s' % login), ('phone', '=', number), ('mobile', '=', number)], limit=1)
        id = 0
        email = 'a***@a***.com'
        phone = '+90 5** *** 1234'
        vat = '90*******00'
        if partner:
            id = request.env['res.partner.otp'].sudo().create({
                'partner_id': partner.id,
                'company_id': partner.company_id.id,
                'lang': partner.lang,
            }).id

            email = partner.email
            if '@' in email and '.' in email:
                name, domain = email.split('@', 1)
                address, suffix = domain.split('.', 1)
                email = '%s***@%s***.%s' % (name[0], address[0], suffix)
            else:
                email = '-'

            phone = partner.mobile or partner.phone
            if phone:
                phone = '+90 5** *** %s' % phone[-4:]
            else:
                phone = '-'

            if partner.child_ids:
                child = partner.child_ids.filtered(lambda x: login in x.vat)
                if child:
                    vat = child.vat
                    vat = '%s******%s' % (vat[:2], vat[-2:0]) if vat else '-'
                else:
                    vat = partner.child_ids[0].vat
                    vat = '%s******%s' % (vat[:2], vat[-2:0]) if vat else '-'
            else:
                vat = '-'

        return {
            'id': id,
            'email': email,
            'phone': phone,
            'vat': vat,
        }

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
