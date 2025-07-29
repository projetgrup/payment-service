# -*- coding: utf-8 -*-

from odoo import http
from odoo.service import common


json_response = http.JsonRequest._json_response
def _json_response(self, result=None, error=None):
    if isinstance(error, dict):
        if 'message' in error and isinstance(error['message'], str):
            error['message'] = error['message'].replace('Odoo', '').strip()
        if 'code' in error and error['code'] == 200:
            error['code'] = 500
            error['http_status'] = 500
        if 'data' in error and http.request.uid != 1:
            del error['data']
    return json_response(self, result=result, error=error)

http.JsonRequest._json_response = _json_response

#common.RPC_VERSION_1 = {
#    'server_version': '1.0',
#    'server_version_info': (1, 0, 0, 'final', 0, ''),
#    'server_serie': '1.0',
#    'protocol_version': 1,
#}


#import werkzeug
#from odoo.addons.web.controllers import main
#class WebClient(main.WebClient):
#    @http.route('/web/webclient/version_info', type='json', auth="none")
#    def version_info(self):
#        return {}
#        return werkzeug.exceptions.NotFound()
