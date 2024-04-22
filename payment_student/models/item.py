# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PaymentItem(models.Model):
    _inherit = 'payment.item'

    @api.depends('transaction_ids.state')
    def _compute_paid_amount(self):
        super()._compute_paid_amount()
        for item in self:
            if item.system == 'student':
                items = self.env['payment.transaction.item'].sudo().search([
                    ('item_id', '=', item.id),
                    ('transaction_id.state', '=', 'done'),
                ])
                item.bursary_amount = sum(items.mapped('bursary_amount'))
                item.sibling_amount = sum(items.mapped('sibling_amount'))
                item.prepayment_amount = sum(items.mapped('prepayment_amount'))
            else:
                item.bursary_amount = 0
                item.sibling_amount = 0
                item.prepayment_amount = 0

    system = fields.Selection(selection_add=[('student', 'Student Payment System')])

    school_id = fields.Many2one('res.student.school', related='child_id.school_id', store=True, readonly=True, ondelete='restrict')
    class_id = fields.Many2one('res.student.class', related='child_id.class_id', store=True, readonly=True, ondelete='restrict')
    bursary_id = fields.Many2one('res.student.bursary', related='child_id.bursary_id', store=True, readonly=True, ondelete='restrict')
    term_id = fields.Many2one('res.student.term', ondelete='restrict')
    payment_type_id = fields.Many2one('res.student.payment.type', ondelete='restrict')
    bursary_amount = fields.Monetary(string='Bursary Discount', compute='_compute_paid_amount', store=True, readonly=True)
    sibling_amount = fields.Monetary(string='Sibling Discount', compute='_compute_paid_amount', store=True, readonly=True)
    prepayment_amount = fields.Monetary(string='Prepayment Discount', compute='_compute_paid_amount', store=True, readonly=True)

    system_student_faculty_id = fields.Many2one('res.student.faculty', related='parent_id.system_student_faculty_id', store=True, readonly=True, ondelete='restrict')
    system_student_department_id = fields.Many2one('res.student.department', related='parent_id.system_student_department_id', store=True, readonly=True, ondelete='restrict')
    system_student_program_id = fields.Many2one('res.student.program', related='parent_id.system_student_program_id', store=True, readonly=True, ondelete='restrict')

    @api.onchange('child_id', 'term_id', 'payment_type_id')
    def _onchange_student_id(self):
        if not self.system == 'student':
            return

        if self.school_id and self.class_id and self.term_id and self.payment_type_id:
            template = self.env['res.student.payment.template'].search([
                ('school_id','=',self.school_id.id),
                '|', ('class_id','=',self.class_id.id), ('class_id','=',False),
                ('term_id','=',self.term_id.id),
                ('payment_type_id','=',self.payment_type_id.id),
                ('company_id','=',self.company_id.id),
            ], limit=1)
            if template:
                self.amount = template.amount

    def _is_student_sibling_paid(self):
        self.ensure_one()
        return self.search_count([
            ('child_id','!=',self.child_id.id),
            ('parent_id','=',self.parent_id.id),
            ('term_id','=',self.term_id.id),
            ('payment_type_id','=',self.payment_type_id.id),
            ('paid','=',True)
        ]) and True or False

    def action_student_payment_table(self):
        self = self.filtered(lambda x: not x.paid)
        if not self:
            raise UserError(_('Payment table can be calculated only for non paid payment items'))
        payment_table = self.env['res.student.payment.table'].sudo().create({
            'table': self.env['ir.ui.view'].sudo()._render_template('payment_student.student_payment_table', {'vals': self.get_student_payment_table()})
        })
        action = self.env.ref('payment_student.action_payment_table').sudo().read()[0]
        action['res_id'] = payment_table.id
        return action

    def get_student_payment_table(self, installment=None):
        company = self.mapped('company_id')
        if not len(company) == 1:
            return False
            #raise UserError(_('Payment table cannot be related to more than one company'))
        
        if any(not system == 'student' for system in self.mapped('system')):
            return False

        currency = company.currency_id
        precision = currency.decimal_places or 2
        student_ids = []
        payment_ids = []
        bursary_ids = []
        students = []
        payments = []
        bursaries = []
        siblings = []
        discounts = []
        subpayments = []
        subsiblings = []
        subbursaries = []
        totals = []

        for line in self:
            student_id = line.child_id
            bursary_id = line.bursary_id
            term_id = line.term_id
            type_id = line.payment_type_id

            if (term_id.id, type_id.id) not in payment_ids:
                payment_ids.append((term_id.id, type_id.id))
                payments.append({
                    'term_id': term_id.id,
                    'type_id': type_id.id,
                    'name': ' | '.join((term_id.name, type_id.name)),
                    'amount': [],
                })

            if bursary_id.id not in bursary_ids:
                bursary_ids.append(bursary_id.id)
                bursaries.append({
                    'id': bursary_id.id,
                    'name': bursary_id.name,
                    'amount': [],
                })

            if student_id.id not in student_ids:
                student_ids.append(student_id.id)
                students.append({
                    'id': student_id.id,
                    'name': student_id.name,
                })

        student_ids.sort()
        payment_ids.sort(key=lambda x: x[0])
        bursary_ids.sort()
        students.sort(key=lambda x: x['id'])
        payments.sort(key=lambda x: (x['term_id'], x['type_id']))
        bursaries.sort(key=lambda x: x['id'])

        for student in student_ids:
            for payment in payments:
                payment['amount'].append({'id': student, 'amount': 0})
            for bursary in bursaries:
                bursary['amount'].append({'id': student, 'amount': 0})
            siblings.append({'id': student, 'amount': 0})
            discounts.append({'id': student, 'amount': 0})
            subpayments.append({'id': student, 'amount': 0})
            subsiblings.append({'id': student, 'amount': 0})
            subbursaries.append({'id': student, 'amount': 0})
            totals.append({'id': student, 'amount': 0})

        discount_single = company._get_student_discount(installment=installment)
        if len(siblings) > 1 or len(siblings) == 1 and any(line._is_student_sibling_paid() for line in self):
            discount_sibling = company.student_discount_sibling_rate if company.student_discount_sibling_active else 0
        else:
            discount_sibling = 0

        for line in self:
            student_id = line.child_id.id
            bursary_id = line.bursary_id.id
            term_id = line.term_id.id
            type_id = line.payment_type_id.id
            amount = line.amount
            discount_amount = discount_single / -100
            sibling_amount = discount_sibling / -100
            bursary_amount = line.bursary_id.percentage / -100

            if company.student_discount_sibling_maximum:
                if sibling_amount > bursary_amount:
                    sibling_amount = 0
                else:
                    bursary_amount = 0

            payment = list(filter(lambda x: x['term_id'] == term_id and x['type_id'] == type_id, payments))[0]
            payment_item = list(filter(lambda x: x['id'] == student_id, payment['amount']))[0]
            payment_item['amount'] += round(amount, precision)

            subpayment_item = list(filter(lambda x: x['id'] == student_id, subpayments))[0]
            subpayment_item['amount'] += round(amount, precision)

            sibling_item = list(filter(lambda x: x['id'] == student_id, siblings))[0]
            sibling_item['amount'] = round(subpayment_item['amount'] * sibling_amount, precision)

            subsibling_item = list(filter(lambda x: x['id'] == student_id, subsiblings))[0]
            subsibling_item['amount'] = round(sibling_item['amount'] + subpayment_item['amount'], precision)

            bursary = list(filter(lambda x: x['id'] == bursary_id, bursaries))[0]
            bursary_item = list(filter(lambda x: x['id'] == student_id, bursary['amount']))[0]
            bursary_item['amount'] = round(subsibling_item['amount'] * bursary_amount, precision)

            subbursary_item = list(filter(lambda x: x['id'] == student_id, subbursaries))[0]
            subbursary_item['amount'] = round(bursary_item['amount'] + subsibling_item['amount'], precision)

            discount_item = list(filter(lambda x: x['id'] == student_id, discounts))[0]
            discount_item['amount'] = round(subbursary_item['amount'] * discount_amount, precision)

            total_item = list(filter(lambda x: x['id'] == student_id, totals))[0]
            total_item['amount'] = round(discount_item['amount'] + subbursary_item['amount'], precision)

        amount = 0
        for payment in payments:
            for i in payment['amount']:
                amount += i['amount']
            payment['amount'].append({'id': 0, 'amount': amount})
            amount = 0

        amount = 0
        for bursary in bursaries:
            for i in bursary['amount']:
                amount += i['amount']
            bursary['amount'].append({'id': 0, 'amount': amount})
        if amount == 0:
            bursaries = False

        amount = 0
        for i in siblings:
            amount += i['amount']
        siblings.append({'id': 0, 'amount': amount})
        if amount == 0:
            siblings = False

        amount = 0
        for i in discounts:
            amount += i['amount']
        discounts.append({'id': 0, 'amount': amount})

        amount = 0
        for i in subpayments:
            amount += i['amount']
        subpayments.append({'id': 0, 'amount': amount})

        amount = 0
        for i in subsiblings:
            amount += i['amount']
        subsiblings.append({'id': 0, 'amount': amount})

        amount = 0
        for i in subbursaries:
            amount += i['amount']
        subbursaries.append({'id': 0, 'amount': amount})

        amount = 0
        for i in totals:
            amount += i['amount']
        totals.append({'id': 0, 'amount': amount})

        return {
            'students': students,
            'payments': payments,
            'bursaries': bursaries,
            'siblings': siblings,
            'discounts': discounts,
            'subpayments': subpayments,
            'subsiblings': subsiblings,
            'subbursaries': subbursaries,
            'totals': totals,
            'discount_single': discount_single,
            'discount_sibling': discount_sibling,
            'has_payment': len(list(filter(lambda x: x != 0, payment_ids))) > 1,
            'has_bursary': len(list(filter(lambda x: x != 0, bursary_ids))) > 0,
            'currency': currency,
        }
