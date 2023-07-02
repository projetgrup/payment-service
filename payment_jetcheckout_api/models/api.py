# -*- coding: utf-8 -*-
import uuid
import secrets
import base64
import hashlib

from odoo import _, api, fields, models


class PaymentPayloxAPI(models.Model):
    _name = 'payment.acquirer.jetcheckout.api'
    _description = 'Paylox API'

    def _compute_name(self):
        for api in self:
            api.name = api.partner_id.name

    @api.depends('hash_id')
    def _compute_hash(self):
        for api in self:
            if api.api_key and api.secret_key:
                id = api.hash_id or 0
                api.hash_key = base64.b64encode(hashlib.sha256(''.join([api.api_key, api.secret_key, str(id)]).encode('utf-8')).digest()).decode('utf-8')
            else:
                api.hash_key = False

    name = fields.Char(compute='_compute_name')
    api_key = fields.Char(string='API Key', readonly=True)
    secret_key = fields.Char(readonly=True)
    hash_id = fields.Integer(string='Hash ID', default=0, store=False, readonly=False)
    hash_key = fields.Char(string='Hash Key', compute='_compute_hash', readonly=True)
    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['company_id'] = self.env.company.id
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for api in res:
            api.api_key = str(uuid.uuid4())
            api.secret_key = secrets.token_hex(16)
        return res
