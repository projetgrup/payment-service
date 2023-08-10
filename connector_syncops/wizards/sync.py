# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class SyncopsSyncWizard(models.TransientModel):
    _name = 'syncops.sync.wizard'
    _description = 'syncOPS Sync Wizard'

    @api.depends('line_ids')
    def _compute_count(self):
        for rec in self:
            rec.count = len(rec.line_ids)

    type = fields.Char()
    refresh = fields.Boolean()
    count = fields.Integer(compute='_compute_count')
    line_ids = fields.One2many('syncops.sync.wizard.line', 'wizard_id', 'Lines', readonly=True)

    def onchange(self, values, field_name, field_onchange):
        return super(SyncopsSyncWizard, self.with_context(recursive_onchanges=False)).onchange(values, field_name, field_onchange)

    @api.onchange('refresh')
    def onchange_refresh(self):
        pass

    def confirm(self):
        return {'type': 'ir.actions.act_window_close'}


class SyncopsSyncWizardLine(models.TransientModel):
    _name = 'syncops.sync.wizard.line'
    _description = 'syncOPS Sync Wizard Lines'

    wizard_id = fields.Many2one('syncops.sync.wizard')
    name = fields.Char(readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
