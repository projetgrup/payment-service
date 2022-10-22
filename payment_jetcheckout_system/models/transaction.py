# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import fields, models

_logger = logging.getLogger(__name__)

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
        self.jetcheckout_send_done_email()
        self.mapped('jetcheckout_item_ids').write({'paid': True, 'paid_date': datetime.now(), 'installment_count': self.jetcheckout_installment_count})

    def jetcheckout_send_done_email(self):
        self.ensure_one()
        try:
            self.env.cr.commit()
            template = self.env.ref('payment_jetcheckout_system.mail_template_transaction_done')
            partner = self.partner_id.commercial_partner_id
            followers = self.env['mail.followers'].search([('res_model', '=', 'res.partner'), ('res_id', '=', partner.id)])
            partners = followers.mapped('partner_id')
            context = self.env.context.copy()
            context['partner'] = partner
            context['tx'] = self
            context['company'] = self.env.company
            context['url'] = self.jetcheckout_website_id.domain
            values = {'mail_server_id': context['company'].mail_server_id.id}
            for partner in partners:
                template.with_context(context).send_mail(partner.id, force_send=True, email_values=values)
        except Exception as e:
            self.env.cr.rollback()
            _logger.error('Sending email for transaction %s is failed\n%s' % (self.reference, e))
