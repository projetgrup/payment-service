# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    student_discount_sibling_active = fields.Boolean(related='company_id.student_discount_sibling_active', readonly=False)
    student_discount_advance_active = fields.Boolean(related='company_id.student_discount_advance_active', readonly=False)
    student_discount_sibling_rate = fields.Float(related='company_id.student_discount_sibling_rate', readonly=False)
    student_discount_sibling_maximum = fields.Boolean(related='company_id.student_discount_sibling_maximum', readonly=False)
    student_discount_advance_ids = fields.One2many(related='company_id.student_discount_advance_ids', readonly=False)
