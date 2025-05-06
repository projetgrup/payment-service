# -*- coding: utf-8 -*-
import json
import logging
from collections import defaultdict

from odoo import fields, models, api, _
from odoo.http import request

_logger = logging.getLogger(__name__)

def _log_sql_value(value):
    if isinstance(value, str):
        return "$$%s$$" % value
    elif isinstance(value, int):
        return "%s" % value
    else:
        return "NULL"

def log(cr, company=None, **values):
    try:
        if company and isinstance(company, int):
            company = request.env['res.company'].sudo().browse(company)
        if not company:
            company = request.env.company
        if not company:
            return
    except:
        return

    names = company.sec_audit_model_ids.mapped('model')
    if 'record' in values:
        if isinstance(values['record'], models.Model):
            if values['record']._name not in names:
                return
            values['record'] = '%s,%s' % (values['record']._name, values['record'].id)
        if isinstance(values['record'], str):
            if values['record'].split(',', 1)[0] not in names:
                return
        else:
            return

    if 'action' not in values:
        values['action'] = 'other'

    actions = company.sec_audit_action_ids.mapped('code')
    if values['action'] not in actions:
        return

    if 'uid' in values:
        values.update({
            'create_uid': values['uid'],
            'write_uid': values['uid'],
        })
        del values['uid']
    else:
        values.update({
            'create_uid': 1,
            'write_uid': 1,
        })

    if values['action'] in ('view', 'close', 'login', 'logout'):
        if values['create_uid'] == 1:
            return

        try:
            with cr.savepoint():
                cr.execute('''
                    UPDATE
                        security_audit
                    SET
                        end_date = NOW() at time zone 'UTC',
                        duration = extract(epoch from ((NOW() at time zone 'UTC') - create_date))/3600
                    WHERE
                        create_uid = %s AND
                        end_date IS NULL AND
                        action = 'view'
                ''', (values['create_uid'],))
        except Exception as e:
            _logger.error(e)

    if 'company_id' not in values:
        values['company_id'] = company.id or None

    keys = values.keys()
    vals = values.values()
    try:
        with cr.savepoint():
            cr.execute('''
                INSERT INTO security_audit (%s, create_date, write_date)
                VALUES (%s, NOW() at time zone 'UTC', NOW() at time zone 'UTC')
                ''' % (', '.join([f'"{k}"' for k in keys]), ', '.join(map(_log_sql_value, vals)))
            )
    except Exception as e:
        _logger.error(e)
        _logger.error('Log cannot be saved. Details as follows:\n%s' % (json.dumps(values, default=str, indent=4),))


class Audit(models.Model):
    _name = 'security.audit'
    _description = 'Audits'
    _order = 'id desc'

    def _compute_name(self):
        for log in self:
            log.name = 'Log #%s' % (log.id or 0,)

    @api.depends('create_date', 'end_date')
    def _compute_duration(self):
        for log in self:
            if log.create_date:
                if log.end_date:
                    value = (log.end_date - log.create_date).total_seconds() / 3600
                else:
                    value = (fields.Datetime.now() - log.create_date).total_seconds() / 3600
            else:
                value = 0.0

            log.time = value
            log.duration = value

    @api.depends('action', 'button')
    def _compute_badge(self):
        self.env.cr.execute('''
            SELECT name, code, icon
            FROM security_audit_action
        ''')
        result = self.env.cr.dictfetchall() or []
        actions = {res['code']: res for res in result}
        for log in self:
            if log.action in actions:
                action = actions[log.action]
                icon = action['icon']
                name = action['name']
                log.badge = '<span class="badge badge-pill o_field_badge o_field_widget o_readonly_modifier" name="badge"><i class="fa fa-%s"/> %s</span>' % (icon, name)
            else:
                log.badge = False

    @api.depends('tracking')
    def _compute_tracking_table(self):
        for log in self:
            if log.tracking:
                tracking = json.loads(log.tracking)
                log.tracking_table = '''<table class="table">%s</table>''' % '\n'.join([f'<tr><td><strong>{t[0]}</strong></td><td>:</td><td>{t[1]}</td><td><i class="fa fa-arrow-right"/></td><td>{t[2]}</td></tr>' for t in tracking])
            else:
                log.tracking_table = False

    @api.depends('download')
    def _compute_download_table(self):
        for log in self:
            if log.download:
                model, fields, ids, domain = json.loads(log.download)
                length = len(ids) if ids else self.env[model].sudo().search_count(domain)

                domain = [('id', 'in', ids)] if ids else domain
                records = self.env[model].sudo().search_read(domain, ['display_name'])
                if len(records) <= 2:
                    records = [rec['display_name'] for rec in records]
                else:
                    records = [records[0]['display_name'], '...', records[-1]['display_name']]

                log.download_table = '''<div class="text-center"><strong>%s</strong> Records</div><table class="table">%s</table>''' % (
                    length,
                    '\n'.join([f'<tr><td class="text-center"><strong>{rec}</strong></td></tr>' for rec in records])
                )
            else:
                log.download_table = False

    @api.model
    def _selection_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    name = fields.Char(string='Name', compute='_compute_name')
    create_uid = fields.Many2one('res.users', string='User', readonly=True)
    create_date = fields.Datetime(string='Date', readonly=True)
    end_date = fields.Datetime(string='End Date', readonly=True)
    time = fields.Float(string='Time', compute='_compute_duration')
    duration = fields.Float(string='Duration', compute='_compute_duration', store=True, readonly=True)
    record = fields.Reference(string='Record', selection='_selection_model', readonly=True)
    view = fields.Char(string='View', readonly=True)
    button = fields.Char(string='Button', readonly=True)
    tracking = fields.Char(string='Tracking', readonly=True)
    download = fields.Char(string='Download', readonly=True)
    tracking_table = fields.Html(string='Tracking Table', compute='_compute_tracking_table', sanitize=False, readonly=True)
    download_table = fields.Html(string='Download Table', compute='_compute_download_table', sanitize=False, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    badge = fields.Html(string='Badge', compute='_compute_badge', compute_sudo=True, sanitize=False)
    action = fields.Char(string='Action', readonly=True)

    def _update_registry(self):
        if self.env.registry.ready and not self.env.context.get('import_file'):
            self._unregister_hook()
            self._register_hook()
            self.env.registry.registry_invalidated = True

    def _register_hook(self):

        def make_create():
            @api.model_create_multi
            def create(self, vals_list, **kw):
                records = create.origin(self, vals_list, **kw)
                for record in records:
                    log(self.env.cr, uid=self.env.uid, action='create', record=record)
                return records
            return create

        def make_write():
            def write(self, vals, **kw):
                keys = []
                values = {}
                for key in vals.keys():
                    if not self._fields[key].relational:
                        keys.append(key)
                if keys:
                    self.env.cr.execute('''
                        SELECT id,%s
                        FROM %s
                        WHERE id IN (%s)
                    ''' % (','.join(keys), self._table, ','.join(map(str, self.ids))))
                    res = self.env.cr.dictfetchall()
                    for rec in res:
                        values[rec['id']] = rec

                write.origin(self, vals, **kw)

                if values:
                    for record in self:
                        tracking = []
                        if record.id in values:
                            value = values[record['id']]
                            for f, v in value.items():
                                if f == 'id':
                                    continue
                                field = self.env['ir.model.fields'].sudo()._get(self._name, f)
                                if not field:
                                    continue
                                if v != vals[f]:
                                    tracking.append((field.field_description, v, vals[f]))
                        if tracking:
                            tracking = json.dumps(tracking, default=str)
                        else:
                            tracking = None
                        log(self.env.cr, uid=self.env.uid, action='write', record=record, tracking=tracking)
                return True
            return write

        def make_unlink():
            def unlink(self, **kwargs):
                for record in self:
                    log(self.env.cr, uid=self.env.uid, action='unlink', record=record)
                return unlink.origin(self, **kwargs)
            return unlink

        patched_models = defaultdict(set)
        def patch(model, name, method):
            if model not in patched_models[name]:
                patched_models[name].add(model)
                ModelClass = model.env.registry[model._name]
                origin = getattr(ModelClass, name)
                method.origin = origin
                wrapped = api.propagate(origin, method)
                wrapped.origin = origin
                setattr(ModelClass, name, wrapped)

        for model in self.env['res.company'].sudo().search([]).mapped('sec_audit_model_ids.model'):
            Model = self.env.get(model)
            patch(Model, 'create', make_create())
            patch(Model, 'write', make_write())
            patch(Model, 'unlink', make_unlink())

    def _unregister_hook(self):
        NAMES = ['create', 'write', 'unlink']
        for Model in self.env.registry.values():
            for name in NAMES:
                try:
                    delattr(Model, name)
                except AttributeError:
                    pass


class AuditAction(models.Model):
    _name = 'security.audit.action'
    _description = 'Audit Actions'

    name = fields.Char(translate=True)
    code = fields.Char()
    icon = fields.Char()


class Import(models.TransientModel):
    _inherit = 'base_import.import'

    def execute_import(self, fields, columns, options, dryrun=False):
        res = super().execute_import(fields, columns, options, dryrun=dryrun)        
        model = self.env['ir.model'].sudo().search([('model', '=', self.res_model)], limit=1)
        view = model.name
        log(request.cr, uid=request.session.uid, action='upload', view=view)
        return res


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, **kwargs):
        for wizard in self:
            record = '%s,%s' % (wizard.model, wizard.res_id)
            log(request.cr, uid=request.session.uid, action='send', record=record)
        return super()._action_send_mail(**kwargs)
