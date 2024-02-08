# -*- coding: utf-8 -*-
from odoo import _
from odoo.http import request, route
from odoo.exceptions import UserError
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller


class PayloxSystemStudentController(Controller):

    def _get_tx_vals(self, **kwargs):
        res = super()._get_tx_vals(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'student':
            items = []
            ids = 'jetcheckout_item_ids' in res and res['jetcheckout_item_ids'][0][2] or False
            if ids:
                payment_ids = request.env['payment.item'].sudo().browse(ids)
                payment_table = payment_ids.get_student_payment_table(installment=int(kwargs['installment']['id']))
                students = {i: 0 for i in payment_ids.mapped('child_id').ids}
                for payment in payment_ids:
                    sid = payment.child_id.id
                    total_amount = 0
                    bursary_amount = 0
                    sibling_amount = 0
                    prepayment_amount = 0

                    if payment_table['payments']:
                        for pay in payment_table['payments']:
                            amount = next(filter(lambda s: s['id'] == sid, pay['amount']), None)
                            total_amount += amount['amount'] if amount else 0

                    if payment_table['bursaries']:
                        for bursary in payment_table['bursaries']:
                            amount = next(filter(lambda s: s['id'] == sid, bursary['amount']), None)
                            bursary_amount += amount['amount'] if amount else 0

                    if payment_table['siblings']:
                        amount = next(filter(lambda s: s['id'] == sid, payment_table['siblings']), None)
                        sibling_amount = amount['amount'] if amount else 0

                    if payment_table['discounts']:
                        amount = next(filter(lambda s: s['id'] == sid, payment_table['discounts']), None)
                        prepayment_amount = amount['amount'] if amount else 0

                    items.append((0, 0, {
                        'item_id': payment.id,
                        'ref': payment.ref,
                        'advance': payment.advance,
                        'amount': total_amount,
                        'bursary_amount': bursary_amount,
                        'sibling_amount': sibling_amount,
                        'prepayment_amount': prepayment_amount,
                    }))

                res['paylox_transaction_item_ids'] = items
        return res

    def _prepare_system(self, company, system, partner, transaction, options={}):
        res = super()._prepare_system(company, system, partner, transaction, options=options)
        if system == 'student':
            installment = transaction and transaction.jetcheckout_installment_count or 0
            res.update({
                'discount_single': company._get_student_discount(installment=installment) if company.student_discount_advance_active else 0,
                'discount_maximum': int(company.student_discount_sibling_maximum) if company.student_discount_sibling_active else 0,
                'discount_sibling': company.student_discount_sibling_rate if company.student_discount_sibling_active else 0,
            })
        return res

    @route('/my/payment', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_system_payment(self, **kwargs):
        values = {}
        if request.env.company.system == 'student':
            values = {
                'no_redirect': True,
                'no_sidebar_buttons': True,
                'partner_label': _('Student'),
            }
        return super().page_system_payment(values=values, **kwargs)

    @route(['/my/payment/query/partner'], type='json', auth='public', website=True)
    def page_system_payment_query_partner(self, **kwargs):
        if not kwargs.get('vat'):
            raise UserError(_('No ID Number has been entered'))

        company = request.env.company
        if company.system == 'student' and company.subsystem == 'student_university':
            result = request.env['syncops.connector'].sudo()._execute('payment_get_partner_list', params={'vat': kwargs['vat']})
            if not result == None and isinstance(result, list) and len(result) > 0:
                res = result[0]
                student = request.env['res.partner'].sudo().search([
                    ('vat', '=', res.get('vat')),
                    '|', ('company_id', '=', False),
                    ('company_id', '=', company.id),
                ], limit=1)

                faculty = False
                if res.get('faculty_code'):
                    faculty = request.env['res.student.faculty'].sudo().search([
                        ('code', '=', res.get('faculty_code')),
                    ])
                    if not faculty and res.get('faculty_name'):
                        faculty = request.env['res.student.faculty'].sudo().create({
                            'name': res.get('faculty_name'),
                            'code': res.get('faculty_code'),
                            'company_id': company.id,
                        })

                department = False
                if res.get('department_code'):
                    department = request.env['res.student.department'].sudo().search([
                        ('code', '=', res.get('department_code')),
                    ])
                    if not department and res.get('department_name'):
                        department = request.env['res.student.department'].sudo().create({
                            'name': res.get('department_name'),
                            'code': res.get('department_code'),
                            'company_id': company.id,
                        })

                program = False
                if res.get('program_code'):
                    program = request.env['res.student.program'].sudo().search([
                        ('code', '=', res.get('program_code')),
                    ])
                    if not program and res.get('program_name'):
                        program = request.env['res.student.program'].sudo().create({
                            'name': res.get('program_name'),
                            'code': res.get('program_code'),
                            'company_id': company.id,
                        })

                if not res.get('email'):
                    email = company.email
                    if not email or '@' not in email:
                        email = 'vat@paylox.io'
                    name, domain = email.rsplit('@', 1)
                    res['email'] = '%s@%s' % (kwargs['vat'], domain)

                values = {
                    'system_student_faculty_id': faculty and faculty.id,
                    'system_student_department_id': department and department.id,
                    'system_student_program_id': program and program.id,
                    'email': res.get('email'),
                    'mobile': res.get('mobile'),
                }

                if student:
                    student.sudo().with_context(skip_student_vat_check=True).write(values)
                else:
                    values.update({
                        'name': ' '.join([res.get('name', ''), res.get('surname', '')]),
                        'vat': kwargs['vat'],
                        'company_id': company.id,
                        'system': 'student',
                    })
                    student = request.env['res.partner'].sudo().with_context(skip_student_vat_check=True).create(values)

            else:
                student = request.env['res.partner'].sudo().search([('vat', '=', kwargs['vat']), ('company_id', '=', company.id)], limit=1)

            if student:
                return {
                    'id': student.id,
                    'name': student.name,
                    'system_student_faculty_id': student.system_student_faculty_id.name,
                    'system_student_department_id': student.system_student_department_id.name,
                    'system_student_program_id': student.system_student_program_id.name,
                    'phone': student.mobile,
                    'email': student.email,
                }

            return {}
        return super().page_system_payment_query_partner(**kwargs)


    #@route(['/my/payment/create/partner'], type='json', auth='public', website=True)
    #def page_system_payment_create_partner(self, **kwargs):
    #    company = request.env.company
    #    if company.system == 'student' and company.subsystem == 'student_university':
    #        return {}
    #    return super().page_system_payment_create_partner(**kwargs)
