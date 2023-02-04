# -*- coding: utf-8 -*-
# Copyright © 2022 Projetgrup (https://www.bulutkobi.io)
# Part of Projetgrup BulutKOBI. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime
from odoo.http import request, route, Controller

_logger = logging.getLogger(__name__)


class PosSync(Controller):

    @route(['/pos/sync'], type='json', auth='user')
    def pos_sync(self, **params):
        sync = request.env['pos.sync'].sudo()
        ids = []

        if params.get('operation') == 'stop':
            sync.search([('name', '=', params['name'])], limit=1).write({'data': False})
            return {}

        if params['orders']:
            for order in params['orders']:
                synced_order = sync.search([('name', '=', order['name'])], limit=1)
                if not synced_order:
                    synced_order = sync.create({
                        'session_id': params['sid'],
                        'cashier_id': params['id'],
                        'name': order['name'],
                        'data': order['data'],
                    })
                else:
                    synced_order.write({
                        'cashier_id': params['id'],
                        'data': order['data'],
                    })
                ids.append(synced_order.id)

        now = datetime.now()
        date = params.get('date') or now
        orders = sync.search_read([('session_id', '=', params['sid']), ('cashier_id', '!=', params['id']), ('id', 'not in', ids), ('write_date', '>', date)], ['name', 'data'])
        return {
            'orders': orders,
            'date': now,
        }
