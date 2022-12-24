# -*- coding: utf-8 -*-
import requests
from odoo import models, _


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _jetcheckout_cancel_postprocess(self):
        super()._jetcheckout_cancel_postprocess()
        self.mapped('jetcheckout_item_ids').write({'bursary_amount': 0, 'prepayment_amount': 0})

    def _jetcheckout_done_postprocess(self):
        super()._jetcheckout_done_postprocess()
        if self.company_id.system == 'student':
            urls = self.company_id.notif_webhook_ids.mapped('url')
            for url in urls:
                requests.post(url, json={
                    'parent': {
                        'name': self.partner_id.name,
                        'vat': self.partner_id.vat,
                    },
                    'items': [{
                        'student': {
                            'name': item.child_id.name,
                            'vat': item.child_id.vat,
                            'ref': item.child_id.ref,
                        },
                        'bursary': {
                            'name': item.bursary_id.name,
                            'code': item.bursary_id.code,
                            'discount': item.bursary_id.percentage,
                        },
                        'amount': {
                            'total': item.amount,
                            'discount': {
                                'bursary': item.bursary_amount,
                                'prepayment': item.prepayment_amount,
                            },
                            'paid': item.paid_amount,
                        }
                    } for item in self.jetcheckout_item_ids],
                    'card': {
                        'family': self.jetcheckout_card_family,
                        'vpos': self.jetcheckout_vpos_name,
                    }
                })
