# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import fields, models

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _compute_item_count(self):
        for tx in self:
            tx.jetcheckout_item_count = len(tx.jetcheckout_item_ids)

    system = fields.Selection(related='company_id.system')
    jetcheckout_item_ids = fields.Many2many('payment.item', 'transaction_item_rel', 'transaction_id', 'item_id', string='Payment Items')
    jetcheckout_item_count = fields.Integer(compute='_compute_item_count')
    jetcheckout_connector_state = fields.Boolean('Connector State', readonly=True)

    def action_items(self):
        self.ensure_one()
        system = self.company_id.system
        action = self.env.ref('payment_%s.action_item' % system).sudo().read()[0]
        action['domain'] = [('id', 'in', self.jetcheckout_item_ids.ids)]
        action['context'] = {'create': False, 'edit': False, 'delete': False}
        return action

    def action_process_connector(self):
        self.ensure_one()
        if not self.jetcheckout_connector_state:
            return

        result = self.env['jconda.connector'].sudo()._execute('post_partner_payment', params={
            'account_name': '108.01',
            'transaction_id': self.jetcheckout_transaction_id,
            'pos_name': self.jetcheckout_vpos_name,
            'date': self.last_state_change.strftime('%Y-%m-%d'),
            'vat': self.partner_id.vat,
            'card_number': self.jetcheckout_card_number,
            'installments': self.jetcheckout_installment_description,
            'currency_name': self.currency_id.name,
            'amount': self.jetcheckout_payment_amount,
            'amount_commission_cost': self.jetcheckout_commission_amount,
            'amount_customer_cost': self.jetcheckout_customer_amount
        }, company=self.company_id)
        self.jetcheckout_connector_state = result == None

    def _jetcheckout_cancel_postprocess(self):
        super()._jetcheckout_cancel_postprocess()
        self.mapped('jetcheckout_item_ids').write({'paid': False, 'paid_date': False, 'paid_amount': 0, 'installment_count': 0})

    def _jetcheckout_done_postprocess(self):
        super()._jetcheckout_done_postprocess()
        self.mapped('jetcheckout_item_ids').write({'paid': True, 'paid_date': datetime.now(), 'installment_count': self.jetcheckout_installment_count})
        self.action_process_connector()
