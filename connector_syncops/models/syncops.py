# -*- coding: utf-8 -*-
import requests
import logging

from odoo import models, api, fields, _
from odoo.exceptions import RedirectWarning, ValidationError, UserError

_logger = logging.getLogger(__name__)

class SyncopsConnector(models.Model):
    _name = 'syncops.connector'
    _description = 'syncOPS Connectors'
    _order = 'id DESC'

    name = fields.Char(required=True)
    username = fields.Char(string='Username', required=True)
    token = fields.Char(string='Token', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, ondelete='cascade', required=True, readonly=True)
    method_ids = fields.One2many('syncops.method', 'connector_id', string='Methods', readonly=True)
    active = fields.Boolean(default=True)
    connected = fields.Boolean(readonly=True)

    @api.constrains('token')
    def _check_token(self):
        for connector in self:
            same_connector = self.sudo().with_context({'active_test': False}).search_count([('id', '!=', connector.id), ('token', '=', connector.token)])
            if same_connector:
                raise UserError(_('This token is already exist. Please ensure that it is correct.'))

    @api.model
    def _count(self, method, company=None):
        if not company:
            company = self.env.company

        return self.search_count([
            ('company_id', '=', company.id),
            ('connected', '=', True),
            ('method_ids.code', '=', method)
        ])

    @api.model
    def _find(self, method, company=None):
        if not company:
            company = self.env.company

        return self.search([
            ('company_id', '=', company.id),
            ('connected', '=', True),
            ('method_ids.code', '=', method)
        ], limit=1)

    @api.model
    def _execute(self, method, params={}, company=None, message=None):
        result = []
        try:
            url = self.env['ir.config_parameter'].sudo().get_param('syncops.url')
            if not url:
                raise ValidationError(_('No syncOPS endpoint URL found'))

            if not company:
                company = self.env.company

            connector = self._find(method, company)
            if not connector:
                raise ValidationError(_('No connector found'))

            url += '/api/v1/execute'
            response = requests.post(url, json={
                'username': connector.username,
                'token': connector.token,
                'method': method,
                'params': params,
            })
            if response.status_code == 200:
                results = response.json()
                if not results['status'] == 0:
                    _logger.error('An error occured when executing method %s for %s: %s' % (method, company and company.name or '', results['message']))
                    return (None, results['message']) if message else None
                result = results.get('result', [])
            else:
                _logger.error('An error occured when executing method %s for %s: %s' % (method, company and company.name or '', response.reason))
                return (None, response.reason) if message else None
        except Exception as e:
            _logger.error('An error occured when executing method %s for %s: %s' % (method, company and company.name or '', e))
            return (None, str(e)) if message else None

        return (result, None) if message else result

    def _connect(self, no_commit=False):
        url = self.env['ir.config_parameter'].sudo().get_param('syncops.url')
        if not url:
            self.write({
                'connected': False,
                'method_ids': [(5, 0, 0)],
            })
            if not no_commit:
                self.env.cr.commit()

            if self.env.user.has_group('base.group_system'):
                action = self.env.ref('connector_syncops.action_syncops_config_settings')
                message = _('You must specify a syncOPS endpoint URL address in settings')
                raise RedirectWarning(message, action.id, _('Go to settings'))
            else:
                raise ValidationError(_('Connection error is occured. Please contact with system administrator.'))

        url += '/api/v1/connect'
        result = {}
        for connector in self:
            try:
                response = requests.post(url, json={'username': connector.username, 'token': connector.token})
                if response.status_code == 200:
                    result = response.json()
                    if result['status'] == 0:
                        connector.write({
                            'connected': True,
                            'method_ids': [(5, 0, 0)] + [(0, 0, {
                                'code': code,
                                'name': name,
                            }) for code, name in result['methods'].items()]
                        })
                        result[connector.id] = {
                            'type': 'info',
                            'title': _('Success'),
                            'message': _('Connection is succesful')
                        }
                    else:
                        connector.write({
                            'connected': False,
                            'method_ids': [(5, 0, 0)],
                        })
                        result[connector.id] = {
                            'type': 'danger',
                            'title': _('Error'),
                            'message': _('An error occured when connecting: %s' % result['message'])
                        }
                else:
                    connector.write({
                        'connected': False,
                        'method_ids': [(5, 0, 0)],
                    })
                    result[connector.id] = {
                        'type': 'danger',
                        'title': _('Error'),
                        'message': _('An error occured when connecting: %s' % response.reason)
                    }
            except Exception as e:
                connector.write({
                    'connected': False,
                    'method_ids': [(5, 0, 0)],
                })
                result[connector.id] = {
                    'type': 'danger',
                    'title': _('Error'),
                    'message': _('An error occured when connecting: %s' % e)
                }
        return result

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._connect(no_commit=True)
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'username' in vals or 'token' in vals:
            self._connect()
        return res

    def action_toggle_active(self):
        self.ensure_one()
        self.active = not self.active

    def action_connect(self):
        self.ensure_one()
        result = self._connect()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
                **result[self.id]
            }
        }

    
class SyncopsMethod(models.Model):
    _name = 'syncops.method'
    _description = 'syncOPS Methods'

    connector_id = fields.Many2one('syncops.connector', 'Connector', index=True, ondelete='cascade')
    name = fields.Char()
    code = fields.Char()
