# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.payment_jetcheckout_system.controllers.main import JetcheckoutSystemController as JetSystemController


class StudentPaymentController(JetSystemController):

    def _jetcheckout_tx_vals(self, **kwargs):
        res = super()._jetcheckout_tx_vals(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'student':
            ids = 'jetcheckout_item_ids' in res and res['jetcheckout_item_ids'][0][2] or False
            if ids:
                payment_ids = request.env['payment.item'].sudo().browse(ids)
                payment_table = payment_ids.get_student_payment_table()
                amounts = payment_table['totals'] if int(kwargs.get('installment', 1)) == 1 else payment_table['subbursaries']

                students = {i: 0 for i in payment_ids.mapped('child_id').ids}
                for payment in payment_ids:
                    sid = payment.child_id.id
                    students[sid] += payment.amount
                for payment in payment_ids:
                    sid = payment.child_id.id
                    first_amount = students[sid]
                    last_amount = list(filter(lambda x: x['id'] == sid, amounts))[0]['amount']
                    rate = last_amount / first_amount if first_amount != 0 else 1
                    payment.paid_amount = payment.amount * rate
                    payment.bursary_amount = payment.amount * payment.bursary_id.percentage / 100 if payment.bursary_id else 0
                    payment.prepayment_amount = payment.amount - payment.paid_amount - payment.bursary_amount
        return res

    def _jetcheckout_system_page_values(self, company, system, partner, transaction):
        res = super()._jetcheckout_system_page_values(company, system, partner, transaction)
        if system == 'student':
            res.update({
                'advance_discount': company.get_student_discount() if company.student_discount_advance_active else 0,
                'maximum_discount': int(company.student_discount_sibling_maximum) if company.student_discount_sibling_active else 0,
                'sibling_discount': company.student_discount_sibling_rate if company.student_discount_sibling_active else 0,
            })
        return res
