# -*- coding: utf-8 -*-
import json
import random
import urllib.request

from odoo.exceptions import ValidationError

class rpc():

    @classmethod
    def _rpc(self, url, method, params):
        data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": random.randint(0, 1000000000),
        }

        req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
        reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
        if reply.get("error"):
            raise ValidationError(reply["error"]["data"]["message"])
        return reply["result"]

    @classmethod
    def _call(self, service, method, url, *args):
        return self._rpc(url, "call", {"service": service, "method": method, "args": args})

    @classmethod
    def execute(self, url, *args):
        return self._rpc(url, "call", {"service": "object", "method": "execute", "args": args})

    @classmethod
    def login(self, url, *args):
        return self._rpc(url, "call", {"service": "common", "method": "login", "args": args})
