# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IrConnector(models.Model):
    _name = 'ir.connector'
    _description = 'Connector'
    _order = 'sequence'

    active = fields.Boolean(default=True)
    sequence = fields.Integer(string='Priority', default=10)
    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    type = fields.Selection([])
    subtype = fields.Many2one('ir.connector.subtype')
    server = fields.Char()
    username = fields.Char()
    password = fields.Char()
    line_ids = fields.One2many('ir.connector.line', 'connector_id', string='Methods', copy=True)

    def _get(self, code, record):
        self.ensure_one()
        line = self.env['ir.connector.line'].search([('connector_id', '=', self.id), ('method_id.code', '=', code)], limit=1)
        if not line:
            raise
        return getattr(self, '_get_%s_%s' % (self.type, code))(line, record)

    def action_test_connection(self):
        if not self.type:
            raise UserError(_('Please select a connector type'))
        if not self.subtype:
            raise UserError(_('Please select a connector subtype'))

        getattr(self, '_test_%s_%s_connection' % (self.type, self.subtype.code))()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Connection is succesful.'),
                'type': 'info',
                'sticky': False,
            }
        }


class IrConnectorLine(models.Model):
    _name = 'ir.connector.line'
    _description = 'Connector Lines'

    connector_id = fields.Many2one('ir.connector')
    method_id = fields.Many2one('ir.connector.line.method')
    procedure = fields.Char(required=True, string='Procedure')
    parameter_ids = fields.One2many('ir.connector.line.mapping', 'line_id', string='Parameters', copy=True, domain=[('type', '=', 'parameter')])
    response_ids = fields.One2many('ir.connector.line.mapping', 'line_id', string='Responses', copy=True, domain=[('type', '=', 'response')])
    model_id = fields.Many2one('ir.model', string='Model')
    company_id = fields.Many2one(related='connector_id.company_id', store=True)


class IrConnectorLineMapping(models.Model):
    _name = 'ir.connector.line.mapping'
    _description = 'Connector Line Mapping'

    def _get_field_type(self, model, key):
        if '.' in key:
            keys = key.split('.')
            field = self.env['ir.model.fields'].search([('model_id.model', '=', model), ('name', '=', keys[0])])
            if not field:
                raise UserError(_('Field %s not found') % keys[0])
            if field.relation: 
                return self._get_field_type(field.relation, '.'.join(keys[1:]))
            raise UserError(_('Field %s is not relational') % keys[0])
        field = self.env['ir.model.fields'].search([('model_id.model', '=', model), ('name', '=', key)])
        if not field:
            raise UserError(_('Field %s not found') % key)
        return field.ttype

    @api.depends('key', 'model_id')
    def _compute_key_type(self):
        for mapping in self:
            mapping.key_type = mapping._get_field_type(mapping.model_id.model, mapping.key)

    line_id = fields.Many2one('ir.connector.line.method')
    type = fields.Selection([('parameter', 'Parameter'), ('response', 'Response')])
    key = fields.Char(required=True)
    key_type = fields.Char(string='Key Type', compute='_compute_key_type', compute_sudo=True)
    value = fields.Char(required=True)
    value_type = fields.Selection([('string', 'String'), ('integer', 'Integer'), ('float', 'Float')], default='string', string='Value Type')
    model_id = fields.Many2one(related='line_id.model_id', store=True)
    company_id = fields.Many2one(related='line_id.company_id', store=True)
