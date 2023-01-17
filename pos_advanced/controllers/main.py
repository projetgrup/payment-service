# -*- coding: utf-8 -*-
# Copyright © 2022 Projetgrup (https://www.bulutkobi.io)
# Part of Projetgrup BulutKOBI. See LICENSE file for full copyright and licensing details.
from odoo.tools.translate import _
from odoo.http import request, route
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


class JetControllerPos(JetController):

    @route(['/pos/bank/prepare'], type='json', auth='user')
    def pos_bank_prepare(self, **kwargs):
        method = request.env['pos.payment.method'].sudo().browse(kwargs.get('method', 0))
        if not method:
            return {'error': _('Method not found')}

        partner = request.env['res.partner'].sudo().browse(kwargs.get('partner', 0))
        if not partner:
            return {'error': _('Partner not found')}

        return {
            'id': partner.id,
            'email': partner.email or '',
            'phone': partner.mobile or '',
            'bank': method.bank or '',
        }

    @route(['/pos/bank/sms'], type='json', auth='user')
    def pos_bank_sms(self, **kwargs):
        if not kwargs['phone']:
            raise ValidationError(_('Please fill phone number'))

        method = request.env['pos.payment.method'].sudo().browse(kwargs.get('method', 0))
        if not method:
            return {'error': _('Method not found')}

        try:
            partner = request.env['res.partner'].sudo().browse(kwargs['partner'])
            template = request.env.ref('pos_advanced.sms_template_banks')
            amount = formatLang(request.env, kwargs['amount'])
            context = {
                'amount': amount,
                'phone': kwargs['phone'],
                'bank': kwargs['bank'],
            }
            template.with_context(context).send_sms(partner, {'phone': kwargs['phone']})
            return _('SMS has been sent successfully')
        except Exception as e:
            return _('SMS has not been sent (%s)' % e)

    @route(['/pos/bank/email'], type='json', auth='user')
    def pos_bank_email(self, **kwargs):
        if not kwargs['email']:
            raise ValidationError(_('Please fill email address'))

        method = request.env['pos.payment.method'].sudo().browse(kwargs.get('method', 0))
        if not method:
            return {'error': _('Method not found')}

        try:
            template = request.env.ref('pos_jetcheckout.mail_template_banks')
            context = {
                'amount': kwargs['amount'],
                'email': kwargs['email'],
                'bank': kwargs['bank'],
                'company': request.env.company,
                'user': request.env.user.partner_id
            }
            template.with_context(context).send_mail(kwargs['partner'], force_send=True, email_values={'is_notification': True})
            return _('Email has been sent successfully')
        except Exception as e:
            return _('Email has not been sent (%s)' % e)
