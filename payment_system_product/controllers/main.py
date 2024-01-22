# -*- coding: utf-8 -*-
from .sse import dispatch
from odoo.http import route, request, Response, Controller


class PaymentProductController(Controller):

    @route(['/longpolling/prices'], type='http', methods=['GET'], auth='public', cors='*')
    def payment_product_price(self, **kwargs):
        return Response(dispatch.poll(request.db, request.env.company.id, request.uid, request.context), headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        })
