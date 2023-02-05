# -*- coding: utf-8 -*-
import json
import datetime
from odoo import api, models
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.bus.models.bus import json_dump, channel_with_db, TIMEOUT


class ImBus(models.Model):
    _inherit = 'bus.bus'

    @api.model
    def _poll(self, channels, last=0, options=None):
        if options is None:
            options = {}

        if last == 0:
            timeout_ago = datetime.datetime.utcnow() - datetime.timedelta(seconds=TIMEOUT)
            domain = [('create_date', '>', timeout_ago.strftime(DEFAULT_SERVER_DATETIME_FORMAT))]
        else:
            domain = [('id', '>', last)]

        if options is not None and options.get('pos'):
            domain.append(('message', 'like', '%pos.bus%'))
        else:
            domain.append(('message', 'not like', '%pos.bus%'))

        channels = [json_dump(channel_with_db(self.env.cr.dbname, c)) for c in channels]
        domain.append(('channel', 'in', channels))
        notifications = self.sudo().search_read(domain)

        result = []
        for notif in notifications:
            result.append({
                'id': notif['id'],
                'message': json.loads(notif['message']),
            })
        return result
