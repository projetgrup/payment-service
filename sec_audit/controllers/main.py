# -*- coding: utf-8 -*-

import json
import logging
import operator
from pytz import timezone
from datetime import datetime

from odoo import http, _
from odoo.http import request, Response, Controller
from odoo.addons.web.controllers.main import WebClient, Home, Session, DataSet, ExcelExport, ensure_db
from odoo.exceptions import AccessError, UserError, ValidationError, MissingError
from ..models.audit import log

_logger = logging.getLogger(__name__)


class AuditController(Controller):

    def _auth(self):
        raise AccessError('Wrong username or password')

    @http.route(['/security/audit/log'], type='json', auth='user')
    def audit_log(self, company, action, view=None, record=None):
        log(request.cr, company=company, uid=request.session.uid, action=action, view=view, record=record)

    @http.route(['/security/audit/get'], type='http', auth='public', methods=['GET'], website=True)
    def audit_get(self, **params):
        try:
            token = self._auth()
            filter = token.company_id.sec_audit_webservice_filter
            domain = json.loads(filter) if filter else []
            domain += [('company_id', '=', token.company_id.id)]
            if params:
                date_offset = timezone('Europe/Istanbul').utcoffset(datetime.now())
                if params.get('date_start'):
                    try:
                        date_start = datetime.strptime(params['date_start'], '%Y-%d-%m %H:%M:%S') - date_offset
                    except Exception:
                        raise UserError(_('Bad start date format'))
                    domain += [('create_date', '>=', date_start)]
                if params.get('date_end'):
                    try:
                        date_end = datetime.strptime(params['date_end'], '%Y-%d-%m %H:%M:%S') - date_offset
                    except Exception:
                        raise UserError(_('Bad end date format'))
                    domain += [('create_date', '<=', date_end)]
            logs = request.env['security.audit'].sudo().search_read(domain, ['create_uid', 'create_date', 'action'])
            for log in logs:
                del log['id']
            logs = [{
                'date': log['create_date'].strftime('%Y-%d-%m %H:%M:%S') if log['create_date'] else None,
                'user': log['create_uid'][1] if log['create_uid'] else None,
                'action': log['action'] or None,
            } for log in logs]
            return Response(json.dumps(logs), status=200, mimetype="application/json")
        except AccessError as e:
            return Response(str(e), status=401, mimetype="application/json")
        except UserError as e:
            return Response(str(e), status=400, mimetype="application/json")
        except ValidationError as e:
            return Response(str(e), status=400, mimetype="application/json")
        except MissingError as e:
            return Response(str(e), status=404, mimetype="application/json")
        except Exception as e:
            _logger.error(e, exc_info=True)
            return Response("Server Error", status=500, mimetype="application/json")


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
