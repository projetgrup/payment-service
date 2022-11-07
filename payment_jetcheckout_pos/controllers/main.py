# -*- coding: utf-8 -*-
# Copyright © 2022 Projetgrup (https://www.bulutkobi.io)
# Part of Projetgrup BulutKOBI. See LICENSE file for full copyright and licensing details.

import json
import werkzeug
import logging

from odoo.tools.translate import _
from odoo.http import Controller, request, route
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as Jetcontroller

_logger = logging.getLogger(__name__)


class PointOfSaleVpos(Controller):

    @route(['/pos/card/success', '/pos/card/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def pos_card_preresult(self, **kwargs):
        kwargs['result_url'] = '/pos/card/result'
        url, tx = Jetcontroller._jetcheckout_process(**kwargs)
        return werkzeug.utils.redirect('%s?=%s' % (url, tx.id))

    @route(['/pos/card/result'], type='http', auth='public', methods=['GET'], csrf=False, website=True, sitemap=False)
    def pos_card_result(self, **kwargs):
        if request.session.get('__jetcheckout_last_tx_id'):
            del request.session['__jetcheckout_last_tx_id']

        tx = request.env['payment.transaction'].sudo().browse(int(kwargs['']))
        return request.render('payment_jetcheckout_pos.payment_result', {
            'result': json.dumps({
                'id': tx.id,
                'state': tx.state,
                'message': tx.state_message.replace('"', '\\"').replace('\n', ' ')
            })
        })
