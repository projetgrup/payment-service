# -*- coding: utf-8 -*-
# Copyright © 2022 Projetgrup (https://www.bulutkobi.io)
# Part of Projetgrup BulutKOBI. See LICENSE file for full copyright and licensing details.
import werkzeug
import base64
from odoo.tools.translate import _
from odoo.http import request, route
from odoo.exceptions import ValidationError
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


class JetControllerPos(JetController):


    @route(['/pos/bank/logo/<int:id>/<string:token>'], type='http', methods=['GET'], auth='public')
    def pos_bank_logo(self, id, token, **kwargs):
        bank = request.env['pos.bank'].sudo().search([('id', '=', id), ('token', '=', token)], limit=1)
        if not bank:
            return werkzeug.exceptions.NotFound()
        
        content = base64.b64decode(bank.logo)
        status, headers, content = request.env['ir.http']._binary_set_headers(200, content, '%s.png' % bank.name, 'image/png', True)
        headers.append(('Content-Length', len(content)))
        response = request.make_response(content, headers)
        return response

    @route(['/pos/bank/prepare'], type='json', auth='user')
    def pos_bank_prepare(self, **kwargs):
        vals = {
            'partner': {},
            'banks': {},
        }

        pids = kwargs.get('partner', 0)
        partner = request.env['res.partner'].sudo().browse(pids)
        if partner:
            vals['partner'] = {
                'id': partner.id,
                'email': partner.email or '',
                'phone': partner.mobile or '',
            }

        bids = kwargs.get('banks', [])
        banks = request.env['pos.bank'].sudo().browse(bids)
        if banks:
            vals['banks'] = [{
                'id': bank.id,
                'name': bank.name or '',
                'logo': bank.logo or '',
                'iban': bank.iban or '',
                'account': bank.account or '',
                'branch': bank.branch or '',
            } for bank in banks]

        return vals

    @route(['/pos/bank/sms'], type='json', auth='user')
    def pos_bank_sms(self, **kwargs):
        if not kwargs['phone']:
            raise ValidationError(_('Please fill phone number'))

        if not kwargs['banks']:
            raise ValidationError(_('Please select at least one bank'))

        banks = request.env['pos.bank'].sudo().browse(kwargs['banks'])
        if not banks:
            raise ValidationError(_('Please select at least one bank'))

        template = request.env.ref('pos_advanced.sms_template_banks')
        context = {
            'company': request.env.company,
            'phone': kwargs['phone'],
            'banks': '\\n'.join(['%s\\n%s\\n' % (bank.name, bank.iban) for bank in banks]),
        }
        template.with_context(context).send_sms(kwargs['partner'], {'phone': kwargs['phone']})
        return _('SMS has been sent successfully')

    @route(['/pos/bank/email'], type='json', auth='user')
    def pos_bank_email(self, **kwargs):
        if not kwargs['email']:
            raise ValidationError(_('Please fill email address'))

        if not kwargs['banks']:
            raise ValidationError(_('Please select at least one bank'))

        banks = request.env['pos.bank'].sudo().browse(kwargs['banks'])
        if not banks:
            raise ValidationError(_('Please select at least one bank'))

        template = request.env.ref('pos_advanced.mail_template_banks')
        context = {
            'email': kwargs['email'],
            'banks': banks,
            'company': request.env.company,
            'user': request.env.user.partner_id
        }
        template.with_context(context).send_mail(kwargs['partner'], force_send=True, email_values={'is_notification': True})
        return _('Email has been sent successfully')
