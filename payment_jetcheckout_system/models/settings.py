# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import json


class PaymentSettings(models.TransientModel):
    _name = 'payment.settings'
    _description = 'Payment Settings'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    def start(self):
        return self.next()

    def copy(self, values):
        raise UserError(_('Cannot duplicate configuration!'), '')

    def next(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def execute(self):
        return self.refresh()

    def cancel(self):
        return self.refresh()

    def refresh(self):
        actions = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
        if actions:
            return actions.read()[0]
        return {}

    def name_get(self):
        action = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
        name = action.name or self._name
        return [(record.id, name) for record in self]
