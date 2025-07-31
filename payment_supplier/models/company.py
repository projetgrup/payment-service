# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('supplier', 'Supplier Payment System')])
    payment_plan_approver_ok = fields.Boolean(string='Enable Payment Plan Approvers')
    payment_plan_approver_ids = fields.One2many('payment.plan.approver', 'company_id', string='Payment Plan Approvers')
