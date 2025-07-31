# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    payment_plan_approver_ok = fields.Boolean(related='company_id.payment_plan_approver_ok', readonly=False)
    payment_plan_approver_ids = fields.One2many(related='company_id.payment_plan_approver_ids', readonly=False)
