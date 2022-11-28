# -*- coding: utf-8 -*-
import requests

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from odoo.tools import config


class JCondaConnector(models.Model):
    _name = 'jconda.connector'
    _description = 'jConda Connectors'
    _order = 'id DESC'

    name = fields.Char(required=True)
    username = fields.Char(string='Username', required=True)
    token = fields.Char(string='Token', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, ondelete='cascade', required=True, readonly=True)
    method_ids = fields.Many2many('jconda.method', 'jconda_connector_method_rel', string='Methods', readonly=True)
    active = fields.Boolean(default=True)
    connected = fields.Boolean()

    def _connect(self):
        url = config.get('jconda_url')
        if not url:
            url = self.env['ir.config_parameter'].sudo().get_param('jconda.url')
        if not url:
            self.write({'connected': False})
            self.env.cr.commit()
            raise ValidationError(_('You must specify a jConda endpoint url in your config file with key "jconda_url" or add it as a system parameter with key "jconda.url"'))

        url += '/api/v1/connect'
        result = {}
        for connector in self:
            response = requests.post(url, json={'username': connector.username, 'token': connector.token})
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == 0:
                    methods = self.env['jconda.method'].sudo().search([('code', 'in', result['methods'])])
                    connector.write({
                        'connected': True,
                        'method_ids': [(6, 0, methods.ids)]
                    })
                    result[connector.id] = {
                        'type': 'info',
                        'title': _('Success'),
                        'message': _('Connection is succesful')
                    }
                else:
                    self.write({'connected': False})
                    result[connector.id] = {
                        'type': 'danger',
                        'title': _('Error'),
                        'message': _('An error occured when connecting: %s' % result['response_message'])
                    }
            else:
                self.write({'connected': False})
                result[connector.id] = {
                    'type': 'danger',
                    'title': _('Error'),
                    'message': _('An error occured when connecting: %s' % response.reason)
                }
        return result

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._connect()
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
            'params': {'sticky': False, **result[self.id]}
        }

    
class JCondaMethod(models.Model):
    _name = 'jconda.method'
    _description = 'jConda Methods'

    name = fields.Char(translate=True)
    code = fields.Char()
