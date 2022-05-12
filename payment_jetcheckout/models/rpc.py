# -*- coding: utf-8 -*-
import json
import random
import urllib.request

from odoo.exceptions import ValidationError
from odoo.tools import config

class rpc():

    @staticmethod
    def _connect():
        url = "https://%s/jsonrpc" % config.get("jetcheckout_host", "app.jetcheckout.com")
        db = config.get("jetcheckout_database", "jetcheckout")
        return url, db

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
    def _call(self, service, method, *args):
        url, db = self._connect()
        return self._rpc(url, "call", {"service": service, "method": method, "args": db + args})

    @classmethod
    def execute(self, *args):
        url, db = self._connect()
        return self._rpc(url, "call", {"service": "object", "method": "execute", "args": [db, *args]})

    @classmethod
    def login(self, *args):
        url, db = self._connect()
        return self._rpc(url, "call", {"service": "common", "method": "login", "args": [db, *args]})
