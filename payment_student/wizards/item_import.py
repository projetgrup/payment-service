# -*- coding: utf-8 -*-

from odoo import fields, models


class PaymentItemImport(models.TransientModel):
    _inherit = 'payment.item.import'

    def _get_row(self, value):
        res = super()._get_row(value)
        res.update({
            'student_term_name': value.get('Student Term Name', False),
        })
        return res

    def _prepare_row(self, line):
        res = super()._prepare_row(line)
        if line.student_term_name:
            term = term.search([('name', '=', line.student_term_name), ('company_id', '=', line.company_id.id)], limit=1)
            if not term:
                term = term.create({
                    'name': line.student_term_name,
                    'company_id': line.company_id.id,
                })
            res.update({
                'term_id': term.id,
            })
        return res


class PaymentItemImportLine(models.TransientModel):
    _inherit = 'payment.item.import.line'

    student_term_name = fields.Char(string='Student Term Name', readonly=True)
