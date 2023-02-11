# -*- coding: utf-8 -*-
# Copyright © 2022 Projetgrup (https://www.bulutkobi.io)
# Part of Projetgrup BulutKOBI. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime
from odoo.http import request, route, Controller

_logger = logging.getLogger(__name__)


class PosSync(Controller):

    @route('/pos/ping', type='http', auth='user')
    def pos_ping(self):
        partner = request.env['res.partner'].sudo().browse(0)
        request.env['bus.bus'].with_context(pos={'session': 1, 'cashier': 1})._sendone(partner, 'pos.bus/all', {'status': 'success'})

    @route(['/pos/sync'], type='json', auth='user')
    def pos_sync(self, **params):
        now = datetime.now()
        date = params.get('date') or now

        if params.get('concurrent'):
            partners = request.env['res.users'].sudo().search([('id', '!=', request.env.uid), ('company_id', '=', request.env.company.id), ('share', '=', False)]).mapped('partner_id')

            messages = []
            if params.get('action') == 'done':
                for partner in partners:
                    messages.append([partner, 'pos.bus/all', {
                        'date': now,
                        'orders': [{
                            'name': params['name'],
                            'data': False,
                        }],
                    }])

            else:
                orders = [{
                    'session': params['sid'],
                    'cashier': params['id'],
                    'name': order['name'],
                    'data': order['data'],
                } for order in params.get('orders', [])]

                messages = []
                for partner in partners:
                    messages.append([partner, 'pos.bus/all', {
                        'date': now,
                        'orders': orders,
                    }])

            request.env['bus.bus'].with_context(pos={'session': params['sid'], 'cashier': params['id']})._sendmany(messages)
            return {}

        else:
            sync = request.env['pos.sync'].sudo()
            ids = []

            if params.get('action') == 'done':
                sync.search([('name', '=', params['name'])], limit=1).write({'data': False})
                return {}

            if params.get('orders'):
                for order in params['orders']:
                    synced = sync.search([('name', '=', order['name'])], limit=1)
                    if not synced:
                        synced = sync.create({
                            'session': params['sid'],
                            'cashier': params['id'],
                            'name': order['name'],
                            'data': order['data'],
                        })
                    else:
                        synced.write({
                            'cashier': params['id'],
                            'data': order['data'],
                        })
                    ids.append(synced.id)

            orders = sync.search_read([('session', '=', params['sid']), ('cashier', '!=', params['id']), ('id', 'not in', ids), ('write_date', '>', date)], ['name', 'data'])

            return {
                'date': now,
                'orders': orders,
            }
