# -*- coding: utf-8 -*-

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    sec_audit_ok = fields.Boolean('Enable Audit Logs')
    sec_audit_action_ids = fields.Many2many('security.audit.action', 'res_company_audit_action_rel', 'company_id', 'action_id', 'Filter Audit Log Actions')
    sec_audit_model_ids = fields.Many2many('ir.model', 'res_company_audit_model_rel', 'company_id', 'model_id', 'Filter Audit Log Models')
    sec_audit_webservice_ok = fields.Boolean('Enable Webservice for Audit Logs')
    sec_audit_webservice_filter = fields.Text('Filter Audit Logs for Webservice')
