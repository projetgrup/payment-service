# -*- coding: utf-8 -*-
from odoo import models, fields
from .company import SUBSYSTEMS


class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    def _compute_system_student_subsystem(self):
        for setting in self:
            setting.system_student_subsystem = setting.company_id.system == 'student' and setting.company_id.subsystem

    def _set_system_student_subsystem(self):
        for setting in self:
            if setting.company_id.system == 'student':
                setting.company_id.subsystem = setting.system_student_subsystem

    student_discount_sibling_active = fields.Boolean(related='company_id.student_discount_sibling_active', readonly=False)
    student_discount_advance_active = fields.Boolean(related='company_id.student_discount_advance_active', readonly=False)
    student_discount_sibling_rate = fields.Float(related='company_id.student_discount_sibling_rate', readonly=False)
    student_discount_sibling_maximum = fields.Boolean(related='company_id.student_discount_sibling_maximum', readonly=False)
    student_discount_advance_ids = fields.One2many(related='company_id.student_discount_advance_ids', readonly=False)

    system_student_subsystem = fields.Selection(selection=SUBSYSTEMS, compute='_compute_system_student_subsystem', inverse='_set_system_student_subsystem', string='System Student Subsystem', readonly=False)
