# -*- coding: utf-8 -*-

import json
import operator

from odoo import http, _
from odoo.http import request, Controller
from odoo.addons.web.controllers.main import WebClient, Home, Session, DataSet, ExcelExport, ensure_db
from ..models.audit import log


class AuditController(Controller):
    @http.route(['/security/audit/log'], type='json', auth='user')
    def audit_log(self, action, view=None, record=None):
        log(request.cr, uid=request.session.uid, action=action, view=view, record=record)


class AuditHomeController(Home):

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        response = super().web_login(*args, **kw)
        if request.httprequest.method == 'POST' and request.params.get('login_success', False) == True:
                log(request.cr, uid=request.session.uid, action='login')
        return response


class AuditDataSetController(DataSet):

    @http.route()
    def call_button(self, model, method, args, kwargs):
        action = super().call_button(model, method, args, kwargs)
        if method and kwargs:
            action_id = kwargs.get('context', {}).get('params', {}).get('action', False)
            view = request.env['ir.actions.actions'].sudo().browse(action_id).name or None
            if view:
                record = 0
                if args and args[0]:
                    record = args[0][0]
                record = '%s,%s' % (model, record)
                button = method.replace('action_', '').replace('_', ' ').capitalize()
                log(request.cr, uid=request.session.uid, action='button', button=button, record=record, view=view)
        return action


class AuditSessionController(Session):

    @http.route()
    def logout(self, redirect='/web'):
        log(request.cr, uid=request.session.uid, action='logout')
        return super().logout(redirect=redirect)

class AuditExcelController(ExcelExport):

    def base(self, data):
        params = json.loads(data)
        model, fields, ids, domain, import_compat = operator.itemgetter('model', 'fields', 'ids', 'domain', 'import_compat')(params)
        download = json.dumps([model, fields, ids, domain], default=str)
        model = request.env['ir.model'].sudo().search([('model', '=', model)], limit=1)
        view = model.name
        log(request.cr, uid=request.session.uid, action='download', download=download, view=view)
        return super().base(data)
