# -*- coding: utf-8 -*
import time
import base64
import logging
from http.client import responses
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

LOG_SERVICES= {}


class PayloxLog(models.Model):
    _name = 'payment.paylox.log'
    _description = 'Paylox Logs'
    _order = 'id DESC'

    def _compute_state(self):
        for log in self:
            log.state = log.status and 'success' or 'error'

    def _compute_request_curl(self):
        for log in self:
            if log.request_data:
                try:
                    url = '%s%s' % (log.get_base_url(), log.request_url)
                    data = log.request_data
                    method = log.request_method
                    authorization = '%s:%s' % (log.auth_id.api_key, log.auth_id.secret_key)
                    authorization = base64.b64encode(authorization.encode('utf-8')).decode('ascii')
                    headers = {"Content-Type": "application/json", "Authorization": "Basic %s" % authorization}
                    headers = " -H ".join(['"{0}: {1}"'.format(k, v) for k, v in headers.items()])
                    command = "curl -X {method} -H {headers} -d '{data}' {url}"
                    log.request_curl = command.format(method=method, headers=headers, data=data, url=url) 
                except:
                    log.request_curl = False
            else:
                log.request_curl = False

    def _compute_response_badge(self):
        for log in self:
            log.response_badge = log.response_code and str(log.response_code)[0] or False

    def _prepare_curl(self, url, method, headers, payload):
        command = "curl -X {method} -H {headers} -d '{data}' {url}"
        data = "{" + ", ".join(['"{0}":"{1}"'.format(k,v) for k,v in payload.items()]) + "}"
        headers = " -H ".join(['"{0}: {1}"'.format(k, v) for k, v in headers.items()])
        return command.format(method=method, headers=headers, data=data, url=url) 

    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, copy=False, index=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False, index=True, default=lambda self: self.env.company)
    transaction_id = fields.Many2one('payment.transaction', string='Transaction', readonly=True, copy=False, index=True)
    acquirer_id = fields.Many2one('payment.acquirer', string='Acquirer', readonly=True, copy=False, index=True)
    service_id = fields.Many2one('payment.paylox.log.service', string='Service', readonly=True, copy=False, index=True)
    reference = fields.Char(string='Reference', readonly=True, copy=False)
    environment = fields.Selection([
        ('T', 'Test'),
        ('P', 'Production'),
    ], string='Environment', readonly=True, copy=False)
    state = fields.Selection([('error', 'Error'), ('success', 'Success')], string='State', compute='_compute_state')
    status = fields.Boolean(string='Success', readonly=True, copy=False)
    message = fields.Text(string='Message', readonly=True, copy=False)
    duration = fields.Float(string='Duration', digits=(16, 2), readonly=True, copy=False)
    request_method = fields.Selection([
        ('post', 'POST'),
        ('get', 'GET'),
        ('put', 'PUT'),
        ('delete', 'DELETE'),
        ('patch', 'PATCH'),
        ('options', 'OPTIONS'),
    ], string='Request Method', readonly=True, copy=False)
    request_url = fields.Text(string='Request URL', readonly=True, copy=False)
    request_data = fields.Text(string='Request Data', readonly=True, copy=False)
    request_curl = fields.Text(string='Request cURL', readonly=True, copy=False, compute='_compute_request_curl')
    response_code = fields.Integer(string='Response Code', readonly=True, copy=False)
    response_message = fields.Char(string='Response Message', readonly=True, copy=False)
    response_data = fields.Text(string='Response Data', readonly=True, copy=False)
    response_badge = fields.Char(string='Response Badge', compute='_compute_response_badge')
    debug_ok = fields.Boolean(string='Show Debug')
    debug_message = fields.Text(string='Debug Message')

    def _value_sql(self, value):
        if isinstance(value, str):
            return "$$%s$$" % value
        elif isinstance(value, int):
            return "%s" % value
        else:
            return "NULL"

    def _value(self, value):
        now = time.time()
        code = value.get('code', 200)
        service = self.get_service(value.get('service'))

        return {
            'company_id': value.get('company', self.env.company.id),
            'partner_id': value.get('partner'),
            'transaction_id': value.get('transaction'),
            'acquirer_id': value.get('acquirer'),
            'service_id': service,
            'environment': value.get('env', 'P'),
            'status': value.get('status'),
            'message': value.get('message'),
            'duration': now - value.get('now', now),
            'debug_message': value.get('debug'),
            'request_method': value.get('method'),
            'request_data': value.get('request'),
            'request_url': value.get('url'),
            'response_message': responses.get(int(code), ''),
            'response_data': value.get('response'),
            'response_code': code,
        }

    def name_get(self):
        return [(log.id, 'Log #%s' % log.id) for log in self]

    def action_toggle_debug(self):
        self.sudo().write({'debug_ok': not self.debug_ok})

    @api.model
    def get_service(self, service):
        if service:
            if service in LOG_SERVICES:
                service = LOG_SERVICES[service]
            else:
                service = self.env['payment.paylox.log.service'].sudo().search([('code', '=', service)], limit=1)
                if service:
                    LOG_SERVICES[service] = service.id
                    service = service.id
        return service

    @api.model
    def get_state(self, company=None):
        if not company:
            company = self.env.company
        log = self.env['ir.config_parameter'].sudo().get_param('paylox.log')
        return log == 'all' or log == 'opt' and company.sudo().payment_log_ok

    @api.model
    def save(self, values):
        with self.env.cr.savepoint():
            try:
                values = self._value(values)
                keys = values.keys()
                vals = values.values()
                self.env.cr.execute('''
                    INSERT INTO payment_paylox_log (%s, create_uid, write_uid, create_date, write_date)
                    VALUES (%s, 1, 1, NOW() at time zone 'UTC', NOW() at time zone 'UTC')
                    ''' % (', '.join(keys), ', '.join(map(self._value_sql, vals)))
                )
            except Exception as e:
                _logger.error('An error occured when logging a payment request: %s' % e)


class PayloxLogService(models.Model):
    _name = 'payment.paylox.log.service'
    _description = 'Paylox Log Services'

    name = fields.Char(translate=True)
    code = fields.Char()
