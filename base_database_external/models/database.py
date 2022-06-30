# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class IrDatabaseExternal(models.Model):
    _name = 'ir.database.external'
    _description = 'External Database Source'
    _order = 'sequence'
    _rec_name = 'type'

    active = fields.Boolean(default=True)
    sequence = fields.Integer(string='Priority', default=10)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    type = fields.Selection([])
    server = fields.Char(required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    database = fields.Char(required=True)
    method_ids = fields.One2many('ir.database.external.method', 'database_id', string='Methods', copy=True)

    def _get(self, method, record):
        self.ensure_one()
        line = self.env['ir.database.external.method'].search([('database_id', '=', self.id), ('name', '=', method)], limit=1)
        if not line:
            raise
        return getattr(self, '_get_%s' % method)(line, record)

    def _get_partner_balance(self, line, partner):
        parameters = []
        for param in line.parameter_ids:
            value = partner.mapped(param.name)[0]
            if param.column == 'string':
                value = "'%s'" % value
            parameters.append('@%s = %s' % (param.remote, value))
        results = getattr(self, '_execute_%s_query' % self.type)(line.procedure, parameters)
        responses = {}
        for resp in line.response_ids:
            if resp.column == 'integer':
                result = int(results[resp.remote])
            elif resp.column == 'float':
                result = float(results[resp.remote])
            else:
                result = str(results[resp.remote])
            responses[resp.name] = result
        return responses

    def action_test_connection(self):
        if not self.type:
            raise UserError(_('Please select a database type'))

        getattr(self, '_test_%s_connection' % self.type)()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Connection is succesful.'),
                'type': 'info',
                'sticky': False,
            }
        }


class IrDatabaseExternalMethod(models.Model):
    _name = 'ir.database.external.method'
    _description = 'External Database Source Methods'

    database_id = fields.Many2one('ir.database.external')
    name = fields.Selection([('partner_balance', 'Partner Balance')], string='Name')
    procedure = fields.Char(required=True, string='Procedure')
    parameter_ids = fields.One2many('ir.database.external.mapping', 'method_id', string='Parameters', copy=True, domain=[('type', '=', 'parameter')])
    response_ids = fields.One2many('ir.database.external.mapping', 'method_id', string='Responses', copy=True, domain=[('type', '=', 'response')])
    company_id = fields.Many2one(related='database_id.company_id', store=True)


class IrDatabaseExternalMapping(models.Model):
    _name = 'ir.database.external.mapping'
    _description = 'External Database Source Mappings'

    method_id = fields.Many2one('ir.database.external.method')
    type = fields.Selection([('parameter', 'Parameter'), ('response', 'Response')])
    column = fields.Selection([('string', 'String'), ('integer', 'Integer'), ('float', 'Float')], default='string')
    name = fields.Char(required=True, string='Name')
    remote = fields.Char(required=True, string='Remote Name')
    company_id = fields.Many2one(related='method_id.company_id', store=True)
