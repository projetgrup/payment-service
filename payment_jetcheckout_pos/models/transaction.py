# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    pos_order_id = fields.Many2one('pos.order', string='PoS Order', readonly=True)
    pos_session_id = fields.Many2one('pos.session', related='pos_order_id.session_id', string='PoS Session', readonly=True)
    pos_order_name = fields.Char(string='PoS Order Name', readonly=True)
    pos_method_id = fields.Many2one('pos.payment.method', string='PoS Payment Method', readonly=True)
    pos_payment_id = fields.Many2one('pos.payment', string='PoS Payment', readonly=True)

    def _paylox_refund_postprocess_values(self, amount=0):
        res = super()._paylox_refund_postprocess_values(amount=amount)
        if self.env.context.get('method'):
            res['pos_method_id'] = self.env.context['method']
        return res

    def _paylox_api_refund(self, amount=0.0, **kwargs):
        if self.env.context.get('skip_request'):
            return self._paylox_refund_postprocess(amount)
        return super()._paylox_api_refund(amount=amount, **kwargs)

    def _prepare_pos_values(self, values={}):
        if 'pos_order_id' in values:
            order = self.env['pos.order'].browse(values['pos_order_id'])
            if order.pos_reference:
                values['pos_order_name'] = order.pos_reference

        if 'pos_payment_id' in values:
            payment = self.env['pos.payment'].browse(values['pos_payment_id'])
            if payment.payment_method_id:
                values['pos_method_id'] = payment.payment_method_id.id

        return values

    @api.model
    def create(self, values):
        values = self._prepare_pos_values(values)
        return super().create(values)

    def write(self, values):
        values = self._prepare_pos_values(values)
        return super().write(values)
