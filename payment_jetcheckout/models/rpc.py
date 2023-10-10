# -*- coding: utf-8 -*-
import json
import random
import logging
import urllib.request

from odoo import models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class rpc():

    @classmethod
    def _rpc(self, url, method, params):
        if params['method'] == 'execute' and isinstance(params['args'][3], models.BaseModel):
            if params['args'][4] in ('create', 'write'):
                params['args'][-1] = self._values(params['args'][3], params['args'][-1])
            params['args'][3] = params['args'][3]._remote_name

        data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": random.randint(0, 1000000000),
        }

        req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
        reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
        if reply.get("error"):
            error = reply["error"]["data"]
            _logger.error(error["debug"])
            raise ValidationError(_('An error occured. %s') % error["message"])
        return reply.get("result")

    @classmethod
    def _call(self, service, method, url, *args):
        return self._rpc(url, "call", {"service": service, "method": method, "args": args})

    @classmethod
    def _values(self, model, values):
        for key, val in values.items():
            field = model._fields[key]
            if field.relational:
                if not val:
                    continue
                elif isinstance(val, int):
                    values[key] = model.env[field.comodel_name].browse(val).res_id
                else:
                    for v in values[key]:
                        if v[1]:
                            v[1] = model.env[field.comodel_name].browse(v[1]).res_id
                        elif v[2]:
                            v[2] = self._values(getattr(model, key), v[2])
        return values

    @classmethod
    def execute(self, url, *args):
        return self._rpc(url, "call", {"service": "object", "method": "execute", "args": [*args]})

    @classmethod
    def login(self, url, *args):
        return self._rpc(url, "call", {"service": "common", "method": "login", "args": [*args]})
