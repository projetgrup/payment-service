# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import uuid
import secrets

class StudentAPI(models.Model):
    _name = 'res.student.api'
    _description = 'Student API'

    def _compute_name(self):
        for api in self:
            api.name = api.partner_id.name

    name = fields.Char(compute='_compute_name')
    api_key = fields.Char(string='API Key', readonly=True)
    secret_key = fields.Char(readonly=True)
    partner_id = fields.Many2one('res.partner', required=True)
    company_id = fields.Many2one('res.company', required=True)
    active = fields.Boolean(default=True)

    @api.model
    def default_get(self, fields):
        res = super(StudentAPI, self).default_get(fields)
        res['company_id'] = self.env.company.id
        return res

    @api.model
    def create(self, vals):
        res = super(StudentAPI, self).create(vals)
        for api in res:
            api.api_key = str(uuid.uuid4())
            api.secret_key = secrets.token_hex(16)
        return res
