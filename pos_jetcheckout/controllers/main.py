# -*- coding: utf-8 -*-
# Copyright © 2022 Projetgrup (https://www.bulutkobi.io)
# Part of Projetgrup BulutKOBI. See LICENSE file for full copyright and licensing details.

import json
import werkzeug
import requests

from odoo.tools.translate import _
from odoo.http import Controller, request, route
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as Jetcontroller


class JetcontrollerPos(Controller):

    @route(['/pos/card/success', '/pos/card/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def pos_card_preresult(self, **kwargs):
        kwargs['result_url'] = '/pos/card/result'
        url, tx = Jetcontroller._jetcheckout_process(**kwargs)
        return werkzeug.utils.redirect('%s?=%s' % (url, tx.id))

    @route(['/pos/card/result'], type='http', auth='user', methods=['GET'], csrf=False, website=True, sitemap=False)
    def pos_card_result(self, **kwargs):
        if request.session.get('__jetcheckout_last_tx_id'):
            del request.session['__jetcheckout_last_tx_id']

        tx = request.env['payment.transaction'].sudo().browse(int(kwargs['']))
        return request.render('pos_jetcheckout.payment_result', {
            'result': json.dumps({
                'id': tx.id,
                'state': tx.state,
                'message': tx.state_message.replace('"', '\\"').replace('\n', ' ')
            })
        })

    @route(['/pos/link/prepare'], type='json', auth='user')
    def pos_link_prepare(self, **kwargs):
        raise Exception(request.httprequest.host_url)
        method = request.env['pos.payment.method'].sudo().browse(kwargs.get('method', 0))
        if not method:
            return {'error': _('Method not found')}
        
        partner = request.env['res.partner'].sudo().browse(kwargs.get('partner', 0))
        if not partner:
            return {'error': _('Partner not found')}

        try:
            response = requests.post('%sapi/v1/payment/create/link' % method.jetcheckout_link_url, json={
                'application_key': method.jetcheckout_link_apikey,
                'hash': method.jetcheckout_link_secretkey,
                'id': partner.id,
                'amount': kwargs.get('amount', 0),
                'order': kwargs.get('order', 0),
                'product': kwargs.get('product', 0),
                'product': kwargs.get('product', 0),
                'card_return_url': request.httprequest.host_url,
            })
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == 0:
                    connector.write({
                        'connected': True,
                        'method_ids': [(5, 0, 0)] + [(0, 0, {
                            'code': code,
                            'name': name,
                        }) for code, name in result['methods'].items()]
                    })
                    result[connector.id] = {
                        'type': 'info',
                        'title': _('Success'),
                        'message': _('Connection is succesful')
                    }
                else:
                    connector.write({
                        'connected': False,
                        'method_ids': [(5, 0, 0)],
                    })
                    result[connector.id] = {
                        'type': 'danger',
                        'title': _('Error'),
                        'message': _('An error occured when connecting: %s' % result['response_message'])
                    }
            else:
                connector.write({
                    'connected': False,
                    'method_ids': [(5, 0, 0)],
                })
                result[connector.id] = {
                    'type': 'danger',
                    'title': _('Error'),
                    'message': _('An error occured when connecting: %s' % response.reason)
                }
        except Exception as e:
            connector.write({
                'connected': False,
                'method_ids': [(5, 0, 0)],
            })
            result[connector.id] = {
                'type': 'danger',
                'title': _('Error'),
                'message': _('An error occured when connecting: %s' % e)
            }


        return {
            'url': partner.access_url,
            'email': partner.email or '',
            'phone': partner.mobile or '',
        }