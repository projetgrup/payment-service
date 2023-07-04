# -*- coding: utf-8 -*-
from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _paylox_cancel_postprocess(self):
        super()._paylox_cancel_postprocess()
        self.mapped('jetcheckout_item_ids').write({
            'bursary_amount': 0,
            'prepayment_amount': 0,
        })

    def _get_notification_webhook_data(self):
        data = super()._get_notification_webhook_data()
        if self.company_id.system == 'student':
            data['items'] = [{
                'student': {
                    'name': item.child_id.name,
                    'vat': item.child_id.vat,
                    'ref': item.child_id.ref,
                },
                'bursary': {
                    'name': item.bursary_id.name if item.bursary_id else None,
                    'code': item.bursary_id.code if item.bursary_id else None,
                    'discount': item.bursary_id.percentage,
                },
                'amount': {
                    'total': item.amount,
                    'discount': {
                        'bursary': item.bursary_amount,
                        'prepayment': item.prepayment_amount,
                    },
                    'installment': {
                        'count': item.installment_count or 1,
                        'amount': item.paid_amount / (item.installment_count or 1),
                    },
                    'paid': item.paid_amount,
                }
            } for item in self.jetcheckout_item_ids]
        return data
