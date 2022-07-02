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
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, ondelete='restrict')
    type = fields.Selection([])
    subtype = fields.Many2one('ir.connector.subtype', required=True, ondelete='restrict')
    server = fields.Char()
    username = fields.Char()
    password = fields.Char()
    line_ids = fields.One2many('ir.connector.line', 'connector_id', string='Methods', copy=True)

    @api.onchange('type')
    def onchange_type(self):
        self.subtype = False

    @api.model
    def execute(self, method_code, record, company=None):
        company = company or self.env.company.id
        line = self.env['ir.connector.line'].search([('company_id', '=', company), ('method_code', '=', method_code)], limit=1)
        if not line:
            raise

        parameters = {}
        for param in line.parameter_ids:
            value = record.mapped(param.key)[0]
            if param.value_type == 'string':
                value = "'%s'" % value
            parameters.update({param.value: value})

        connector = line.connector_id
        subtype = connector.subtype
        result = getattr(connector, '_execute_%s_%s_query' % (subtype.type, subtype.code))(line.procedure, parameters)

        responses = {}
        for resp in line.response_ids:
            if resp.value_type == 'integer':
                responses.update({resp.value: int})
            elif resp.value_type == 'float':
                responses.update({resp.value: float})
            else:
                responses.update({resp.value: str})

        results = []
        for res in result:
            value = {}
            for key, val in res.items():
                value.update({key: responses[key](val)})
            results.append(value)
        return results

    def action_test(self):
        if not self.type:
            raise UserError(_('Please select a connector type'))
        if not self.subtype:
            raise UserError(_('Please select a connector subtype'))

        getattr(self, '_test_%s_%s_connection' % (self.type, self.subtype.code))()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Connection is succesful'),
                'type': 'info',
                'sticky': False,
            }
        }


class IrConnectorSubtype(models.Model):
    _name = 'ir.connector.subtype'
    _description = 'Connector Subtypes'

    active = fields.Boolean(default=True)
    name = fields.Char(translate=True)
    code = fields.Char()
    type = fields.Selection([])


class IrConnectorMethod(models.Model):
    _name = 'ir.connector.method'
    _description = 'Connector Methods'

    active = fields.Boolean(default=True)
    name = fields.Char(translate=True, required=True)
    code = fields.Char(required=True)
    model_id = fields.Many2one('ir.model')
    description = fields.Html(sanitize=False)
    parameter_ids = fields.One2many('ir.connector.line.mapping', 'method_id', string='Parameters', domain=[('type', '=', 'parameter')])
    response_ids = fields.One2many('ir.connector.line.mapping', 'method_id', string='Responses', domain=[('type', '=', 'response')])


class IrConnectorLine(models.Model):
    _name = 'ir.connector.line'
    _description = 'Connector Lines'

    connector_id = fields.Many2one('ir.connector', ondelete='cascade')
    method_id = fields.Many2one('ir.connector.method', ondelete='restrict', required=True)
    method_code = fields.Char(related='method_id.code', store=True)
    procedure = fields.Char(required=True, string='Procedure')
    parameter_ids = fields.One2many('ir.connector.line.mapping', 'line_id', string='Parameters', domain=[('type', '=', 'parameter')])
    response_ids = fields.One2many('ir.connector.line.mapping', 'line_id', string='Responses', domain=[('type', '=', 'response')])
    company_id = fields.Many2one(related='connector_id.company_id', store=True)
    model_id = fields.Many2one(related='method_id.model_id')
    description = fields.Html(related='method_id.description')

    @api.onchange('method_id')
    def onchange_method_id(self):
        parameters = [(5, 0, 0)]
        responses = [(5, 0, 0)]
        if self.method_id:
            parameters.extend([(0, 0, {
                'type': line.type,
                'key': line.key,
                'key_type': line.key_type,
                'value': line.value,
                'value_type': line.value_type,
            }) for line in self.method_id.parameter_ids])
            responses.extend([(0, 0, {
                'type': line.type,
                'key': line.key,
                'key_type': line.key_type,
                'value': line.value,
                'value_type': line.value_type,
            }) for line in self.method_id.response_ids])
        return {'value': {'parameter_ids': parameters, 'response_ids': responses}}

    def action_test(self):
        pass

    def action_reset(self):
        pass


class IrConnectorLineMapping(models.Model):
    _name = 'ir.connector.line.mapping'
    _description = 'Connector Line Mapping'

    def _get_field_type(self, key, model):
        if '.' in key:
            keys = key.split('.')
            field = self.env['ir.model.fields'].search([('model_id.model', '=', model), ('name', '=', keys[0])])
            if not field:
                raise UserError(_('Field %s is not found in model %s') % (keys[0], model))
            if field.relation: 
                return self._get_field_type('.'.join(keys[1:]), field.relation)
            raise UserError(_('Field %s is not relational in model %s') % (keys[0], model))
        field = self.env['ir.model.fields'].search([('model_id.model', '=', model), ('name', '=', key)])
        if not field:
            raise UserError(_('Field %s is not found in model %s') % (key, model))
        return field.ttype

    line_id = fields.Many2one('ir.connector.line', ondelete='cascade')
    method_id = fields.Many2one('ir.connector.method', ondelete='cascade')
    type = fields.Selection([('parameter', 'Parameter'), ('response', 'Response')])
    key = fields.Char(required=True)
    key_type = fields.Char(string='Key Type', readonly=True)
    value = fields.Char(required=True)
    value_type = fields.Selection([('string', 'string'), ('integer', 'integer'), ('float', 'float'), ('boolean', 'boolean'), ('date', 'date'), ('datetime', 'datetime')], default='string', string='Value Type')
    company_id = fields.Many2one(related='line_id.company_id', store=True)

    @api.onchange('key')
    def onchange_key(self):
        model = self.line_id.model_id.model if self.line_id else self.method_id.model_id.model if self.method_id else False
        key = self.key if model and self.type == 'parameter' else False
        self.key_type = self._get_field_type(key, model) if key else False
