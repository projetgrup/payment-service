# -*- coding: utf-8 -*-
import threading
import selectors
import contextlib
from time import mktime
from datetime import datetime, timedelta

import odoo
import odoo.service.server as servermod
from odoo import api, SUPERUSER_ID

TIMEOUT = 50


class ServerSentEvents(threading.Thread):

    def __init__(self):
        super().__init__(daemon=True, name=f'{__name__}.SSE')

    def poll(self, db, cid, uid, ctx):
        yield 'retry: 10000\n\n' # 10 sec

        registry = odoo.registry(db)

        with contextlib.suppress(RuntimeError):
            if not self.is_alive():
                self.start()

        with odoo.sql_db.db_connect('postgres').cursor() as cr, selectors.DefaultSelector() as sel:
            conn = cr._cnx
            cr.execute('listen sse')
            cr.commit()
            sel.register(conn, selectors.EVENT_READ)

            while not stop_event.is_set():
                if sel.select(TIMEOUT):
                    conn.poll()
                    while conn.notifies:
                        conn.notifies.pop()
                        now = datetime.utcnow()
                        with registry.cursor() as cur:
                            env = api.Environment(cur, SUPERUSER_ID, {})

                            products = env['product.product'].sudo().with_context(ctx).search([('write_date', '>', now - timedelta(minutes=1))])
                            if products:
                                products += env['product.product'].sudo().with_context(ctx).search([('payment_price_method_product_id', 'in', products.mapped('product_tmpl_id').ids)])
                                data = ['id:%s' % int(mktime(now.timetuple()))]
                                for product in products:
                                    data.append('data:%s;%s' % (product.id, product.price))
                                yield '%s\n\n' % '\n'.join(data)

dispatch = ServerSentEvents()
stop_event = threading.Event()
if servermod.server:
    servermod.server.on_stop(stop_event.set)
