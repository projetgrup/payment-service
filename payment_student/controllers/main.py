# -*- coding: utf-8 -*-
import werkzeug
from datetime import datetime

from odoo import http, _
from odoo.http import request
from odoo.tools.misc import get_lang
from odoo.addons.payment_jetcheckout.controllers.main import jetcheckoutController as jetController

class StudentPaymentController(jetController):

    def jetcheckout_tx_vals(self, **kwargs):
        res = super().jetcheckout_tx_vals(**kwargs)
        ids = kwargs.get('payment_ids',[])
        if ids:
            payment_ids = request.env['res.student.payment'].sudo().browse(ids)
            payment_table = payment_ids.get_payment_table()
            amounts = payment_table['totals'] if int(kwargs.get('installment', 1)) == 1 else payment_table['subbursaries']

            students = {i: 0 for i in set(payment_ids.mapped('student_id').ids)} # mapped olunca set zaten çalışıyor mu?
            for payment in payment_ids:
                sid = payment.student_id.id
                students[sid] += payment.amount
            for payment in payment_ids:
                sid = payment.student_id.id
                first_amount = students[sid]
                last_amount = list(filter(lambda x: x['id'] == sid, amounts))[0]['amount']
                rate = last_amount / first_amount if first_amount != 0 else 1
                payment.paid_amount = payment.amount * rate
            res.update({
                'student_payment_ids': [(6, 0, ids)],
            })
        return res

    @http.route('/p/<int:parent_id>/<string:access_token>', type='http', auth='public', methods=['GET'], csrf=False, sitemap=False, website=True)
    def student_payment_page(self, parent_id, access_token, **kwargs):
        parent = request.env['res.partner'].sudo().browse(parent_id)
        if not parent or not parent.access_token == access_token:
            return werkzeug.utils.redirect('/404')

        tx = None
        if 'x' in kwargs:
            tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id','=',kwargs.get('x'))], limit=1)
            if not tx:
                return werkzeug.utils.redirect('/404')

        company = request.env.company
        currency = company.currency_id
        lang = get_lang(request.env)
        setting = request.env['res.student.setting'].get_settings()
        acquirer = jetController.jetcheckout_get_acquirer(jetController, providers=['jetcheckout'], limit=1)
        card_family = jetController.jetcheckout_get_card_family(jetController, acquirer)

        values = {
            'parent': parent,
            'partner_id': parent.id,
            'company': company,
            'website': request.website,
            'currency': currency,
            'currency_separator' : lang.decimal_point,
            'currency_thousand' : lang.thousands_sep,
            'acquirer': acquirer,
            'card_family': card_family,
            'footer': setting.website_footer if setting else '',
            'advance_discount': setting.get_setting_discount() if setting else 0,
            'maximum_discount': int(setting.discount_maximum) if setting else 0,
            'sibling_discount': setting.discount_sibling if setting and setting.is_discount_sibling else 0,
            'success_url': '/p/%s/%s/success' % (parent_id, access_token),
            'fail_url': '/p/%s/%s/fail' % (parent_id, access_token),
            'tx': tx,
        }
        return request.render('payment_student.student_payment_page', values)

    @http.route('/p/<int:parent_id>/<string:access_token>/<string:status>', type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def student_payment_result(self, parent_id, access_token, status, **kwargs):
        if 'order_id' not in kwargs:
            return werkzeug.utils.redirect('/404')

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id','=',kwargs.get('order_id'))], limit=1)
        if not tx:
            return werkzeug.utils.redirect('/404')

        result_url = '/p/%s/%s?x=%s' % (parent_id, access_token, kwargs.get('order_id'))
        if int(kwargs.get('response_code')) == 0:
            tx.write({'state': 'done'})
            tx.student_payment_ids.write({'paid': True, 'paid_date': datetime.now()})
        else:
            tx.write({
                'state': 'error',
                'state_message': _('%s (Error Code: %s)') % (kwargs.get('message', '-'), kwargs.get('response_code','')),
            })
        return werkzeug.utils.redirect(result_url)

    @http.route(['/p/privacy'], type='json', auth='public', website=True, csrf=False)
    def student_privacy_policy(self):
        setting = request.env['res.student.setting'].get_settings()
        if setting:
            return setting.privacy_policy
        return ''

    @http.route(['/p/agreement'], type='json', auth='public', website=True, csrf=False)
    def student_sale_agreement(self):
        setting = request.env['res.student.setting'].get_settings()
        if setting:
            return setting.sale_agreement
        return ''

    @http.route(['/p/membership'], type='json', auth='public', website=True, csrf=False)
    def student_membership_agreement(self):
        setting = request.env['res.student.setting'].get_settings()
        if setting:
            return setting.membership_agreement
        return ''

    @http.route(['/p/contact'], type='json', auth='public', website=True, csrf=False)
    def student_contact_page(self):
        setting = request.env['res.student.setting'].get_settings()
        if setting:
            return setting.contact_page
        return ''

    @http.route(['/pay'], type='http', auth='user')
    def jetcheckout_payment_page(self, **kwargs):
        return werkzeug.utils.redirect('/404')
