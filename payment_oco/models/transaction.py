# -*- coding: utf-8 -*-
from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _paylox_query(self, values={}):
        if values and self.company_id.system == 'oco':
            values.update({'preauth': True})
        return super()._paylox_query(values=values)

    def _paylox_system_oco_postprocess(self):
        if not self.sale_order_ids and getattr(self, 'jetcheckout_api_product_ids', False):
            self = self.with_company(self.company_id)
            self.sale_order_ids = [(0, 0, {
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'order_line': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                }) for line in self.jetcheckout_api_product_ids]
            })]
            self.sale_order_ids.onchange_partner_id()
            for line in self.sale_order_ids.order_line:
                line.product_id_change()

    def _paylox_auth_postprocess(self):
        if self.company_id.system == 'oco':
            self._paylox_system_oco_postprocess()
        return super()._paylox_auth_postprocess()

    def _paylox_done_postprocess(self):
        if self.company_id.system == 'oco':
            self._paylox_system_oco_postprocess()
        return super()._paylox_done_postprocess()
