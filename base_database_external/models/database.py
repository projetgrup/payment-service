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
    type = fields.Selection([], string='Type')
    server = fields.Char(required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    database = fields.Char(required=True)

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