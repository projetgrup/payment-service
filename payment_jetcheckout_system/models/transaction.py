# -*- coding: utf-8 -*-
from odoo import fields, models
from datetime import datetime

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _compute_item_count(self):
        for tx in self:
            tx.jetcheckout_item_count = len(tx.jetcheckout_item_ids)

    system = fields.Selection(related='company_id.system')
    jetcheckout_item_ids = fields.Many2many('payment.item', 'transaction_item_rel', 'transaction_id', 'item_id', string='Payment Items')
    jetcheckout_item_count = fields.Integer(compute='_compute_item_count')

    def action_items(self):
        self.ensure_one()
        system = self.company_id.system
        action = self.env.ref('payment_%s.action_item' % system).sudo().read()[0]
        action['domain'] = [('id', 'in', self.jetcheckout_item_ids.ids)]
        action['context'] = {'create': False, 'edit': False, 'delete': False}
        return action

    def _jetcheckout_cancel_postprocess(self):
        super()._jetcheckout_cancel_postprocess()
        self.mapped('jetcheckout_item_ids').write({'paid': False, 'paid_date': False, 'paid_amount': 0, 'installment_count': 0})

    def _jetcheckout_done_postprocess(self):
        super()._jetcheckout_done_postprocess()
        self.mapped('jetcheckout_item_ids').write({'paid': True, 'paid_date': datetime.now(), 'installment_count': self.jetcheckout_installment_count})
