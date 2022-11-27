# -*- coding: utf-8 -*-
from odoo import models, fields, _


class JCondaConnector(models.Model):
    _name = 'jconda.connector'
    _description = 'jConda Connectors'
    _order = 'id DESC'

    name = fields.Char(required=True)
    api_key = fields.Char(string='API Key', required=True)
    secret_key = fields.Char(string='Secret Key')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, ondelete='cascade', required=True, readonly=True)
    method_ids = fields.Many2many('jconda.method', 'jconda_connector_method_rel', string='Methods')
    active = fields.Boolean(default=True)

    def action_toggle_active(self):
        self.active = not self.active

    
class JCondaMethod(models.Model):
    _name = 'jconda.method'
    _description = 'jConda Methods'

    name = fields.Char(translate=True)
    code = fields.Char()
