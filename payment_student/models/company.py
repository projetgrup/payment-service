# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('student', 'Student Payment System')])
    student_discount_sibling_active = fields.Boolean(string='Sibling Discount')
    student_discount_advance_active = fields.Boolean(string='Advance Discount')
    student_discount_sibling_rate = fields.Float(string='Sibling Discount Rate')
    student_discount_sibling_maximum = fields.Boolean(string='Sibling Discount Maximum')
    student_discount_advance_ids = fields.One2many('res.student.discount', 'company_id', string='Advance Payment Discounts')

    system_student_type = fields.Selection([
        ('school', 'School'),
        ('university', 'University'),
    ])

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

    def write(self, values):
        if 'system_student_type' in values:
            if not values['system_student_type']:
                values['system_student_type'] = 'school' # Default student system type

        res = super().write(values)

        if 'system_student_type' in values:
            self._update_system_student_type(values['system_student_type'])

        return res

    def _update_system_student_type(self, type=None, users=None):
        group_school = self.env.ref('payment_student.group_type_school')
        group_university = self.env.ref('payment_student.group_type_university')
        for company in self:
            if not users:
                users = self.env['res.users'].sudo().with_context(active_test=False).search([
                    ('share', '=', False),
                    ('company_id', '=', company.id),
                ])
            if not type:
                type = company.system_student_type

            if type == 'university':
                users.write({'groups_id': [(4, group_university.id), (3, group_school.id)]})
            else:
                users.write({'groups_id': [(4, group_school.id), (3, group_university.id)]})
