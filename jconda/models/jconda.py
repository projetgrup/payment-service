# -*- coding: utf-8 -*-
from odoo import models, fields, _


class JCondaConnector(models.Model):
    _name = 'jconda.connector'
    _description = 'jConda Connectors'
    _order = 'id DESC'

    name = fields.Char(required=True)
    api_key = fields.Char(string='API Key', required=True)
    secret_key = fields.Char(string='Secret Key', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, ondelete='cascade', required=True, readonly=True)
    active = fields.Boolean(default=True)

    
class JCondaConnectorLine(models.Model):
    _name = 'jconda.connector.line'
    _description = 'jConda Connector Lines'

    name = fields.Char()
