# -*- coding: utf-8 -*-
import requests
from datetime import datetime
from odoo import fields, models, _


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _compute_item_count(self):
        for tx in self:
            tx.jetcheckout_item_count = len(tx.jetcheckout_item_ids)

    system = fields.Selection(related='company_id.system')
    jetcheckout_item_ids = fields.Many2many('payment.item', 'transaction_item_rel', 'transaction_id', 'item_id', string='Payment Items')
    jetcheckout_item_count = fields.Integer(compute='_compute_item_count')
    jetcheckout_webhook_ok = fields.Boolean('Webhook Notification', readonly=True)
    jetcheckout_webhook_state = fields.Boolean('Webhook Notification State', readonly=True)
    jetcheckout_webhook_state_message = fields.Text('Webhook Notification State Message', readonly=True)
    jetcheckout_webhook_failed_ids = fields.Many2many('payment.settings.notification.webhook', 'transaction_webhook_rel', 'transaction_id', 'webhook_id', string='Failed Webhook Notifications', readonly=True)
    jetcheckout_partner_user_id = fields.Many2one('res.users', 'Sales Representative', related='partner_id.user_id', store=True, readonly=True, ondelete='set null')
    jetcheckout_partner_team_id = fields.Many2one('crm.team', 'Sales Team', related='partner_id.team_id', store=True, readonly=True, ondelete='set null')
    jetcheckout_partner_categ_ids = fields.Many2many('res.partner.category', 'transaction_partner_category_rel', 'transaction_id', 'category_id', 'Tags', related='partner_id.category_id', store=True, readonly=True, ondelete='set null')

    def action_items(self):
        self.ensure_one()
        system = self.company_id.system
        action = self.env.ref('payment_%s.action_item' % system).sudo().read()[0]
        action['domain'] = [('id', 'in', self.jetcheckout_item_ids.ids)]
        action['context'] = {'create': False, 'edit': False, 'delete': False}
        return action

    def action_process_notification_webhook(self):
        self.ensure_one()
        if not self.jetcheckout_webhook_ok or not self.jetcheckout_webhook_state:
            return

        webhooks = self.jetcheckout_webhook_failed_ids
        if not webhooks:
            self.write({
                'jetcheckout_webhook_ok': True,
                'jetcheckout_webhook_state': True,
                'jetcheckout_webhook_state_message': _('This transaction is successfully notified.')
            })
            return

        message = []
        json = self._get_notification_webhook_data()
        for webhook in webhooks:
            try:
                response = requests.post(webhook.url, json=json, timeout=10)
                if response.ok:
                    self.write({'jetcheckout_webhook_failed_ids': [(3, webhook.id, 0)]})
                else:
                    message.append(_('URL %s could not be notified: %s') % (webhook.url, response.reason))

            except Exception as e:
                message.append(_('URL %s could not be notified: %s') % (webhook.url, e))

        if message:
            self.write({
                'jetcheckout_connector_state': True,
                'jetcheckout_connector_state_message': _('This transaction has not been successfully notified.\n%s') % '\n'.join(message)
            })
        else:
            self.write({
                'jetcheckout_connector_state': False,
                'jetcheckout_connector_state_message': _('This transaction has been successfully notified.')
            })

    def _get_notification_webhook_data(self):
        return {
            'parent': {
                'name': self.partner_id.name,
                'vat': self.partner_id.vat,
            },
            'items': [{
                'child': {
                    'name': item.child_id.name,
                    'vat': item.child_id.vat,
                    'ref': item.child_id.ref,
                },
                'amount': {
                    'total': item.amount,
                    'discount': {
                        'prepayment': item.prepayment_amount,
                    },
                    'installment': {
                        'count': item.installment_count or 1,
                        'amount': item.paid_amount / (item.installment_count or 1),
                    },
                    'paid': item.paid_amount,
                }
            } for item in self.jetcheckout_item_ids],
            'card': {
                'family': self.jetcheckout_card_family,
                'vpos': self.jetcheckout_vpos_name,
            }
        }

    def _jetcheckout_cancel_postprocess(self):
        super()._jetcheckout_cancel_postprocess()
        self.mapped('jetcheckout_item_ids').write({'paid': False, 'paid_date': False, 'paid_amount': 0, 'installment_count': 0})

    def _jetcheckout_done_postprocess(self):
        super()._jetcheckout_done_postprocess()
        self.mapped('jetcheckout_item_ids').write({'paid': True, 'paid_date': datetime.now(), 'installment_count': self.jetcheckout_installment_count})

        webhooks = self.company_id.notif_webhook_ids
        if webhooks:
            self.write({
                'jetcheckout_webhook_ok': True,
                'jetcheckout_webhook_failed_ids': [(6, 0, webhooks.ids)],
                'jetcheckout_webhook_state': True,
                'jetcheckout_webhook_state_message': _('This transaction has not been notified yet.')
            })
            self.action_process_notification_webhook()
