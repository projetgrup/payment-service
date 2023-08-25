# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date

SUBSYSTEMS = [
    ('student_school', 'School'),
    ('student_university', 'University'),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('student', 'Student Payment System')])
    subsystem = fields.Selection(selection_add=SUBSYSTEMS)
    student_discount_sibling_active = fields.Boolean(string='Sibling Discount')
    student_discount_advance_active = fields.Boolean(string='Advance Discount')
    student_discount_sibling_rate = fields.Float(string='Sibling Discount Rate')
    student_discount_sibling_maximum = fields.Boolean(string='Sibling Discount Maximum')
    student_discount_advance_ids = fields.One2many('res.student.discount', 'company_id', string='Advance Payment Discounts')

    def _get_student_discount_line(self):
        today = date.today()
        return self.env['res.student.discount'].sudo().search([
            ('company_id','=',self.id),
            '|',('date_start','=',False),('date_start','<=',today),
            '|',('date_end','=',False),('date_end','>=',today),
        ], limit=1, order='id desc')

    def get_student_discount(self):
        self.ensure_one()
        line = self._get_student_discount_line()
        return line.percentage if line else 0
