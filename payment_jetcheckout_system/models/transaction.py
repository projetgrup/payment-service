# -*- coding: utf-8 -*-
import base64
import logging
import requests
import traceback
from pytz import timezone
from urllib.parse import urlparse
from datetime import datetime, timedelta

from odoo import fields, models, api, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError, MissingError
from odoo.addons.payment import utils as payment_utils
from odoo.tools.safe_eval import safe_eval, json as _json, pytz as _pytz, datetime as _datetime

from .settings import DAYS

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _name = 'payment.transaction'
    _inherit = ['payment.transaction', 'mail.thread']

    def _compute_item_count(self):
        for tx in self:
            tx.paylox_item_count = len(tx.jetcheckout_item_ids)

    def _compute_jetcheckout_can_export_txt(self):
        for tx in self:
            tx.jetcheckout_can_export_txt = tx.company_id.root_id.payment_transaction_export_txt

    state = fields.Selection(tracking=True)
    system = fields.Selection(related='company_id.system')

    paylox_item_count = fields.Integer(compute='_compute_item_count')
    paylox_item_tag_id = fields.Many2one('payment.settings.campaign.tag', 'Payment Item Tag', readonly=True, copy=False)
    paylox_item_tag_name = fields.Char('Payment Item Tag Name', readonly=True, copy=False)
    paylox_item_tag_code = fields.Char('Payment Item Tag Code', readonly=True, copy=False)
    paylox_prepayment_amount = fields.Monetary('Prepayment Amount', readonly=True, copy=False)
    paylox_sale_ref = fields.Char('Sale Reference', readonly=True, copy=False)
    paylox_transaction_item_ids = fields.One2many('payment.transaction.item', 'transaction_id', string='Transaction Items')

    jetcheckout_can_export_txt = fields.Boolean('Can Export TXT', compute='_compute_jetcheckout_can_export_txt')
    jetcheckout_item_ids = fields.Many2many('payment.item', 'transaction_item_rel', 'transaction_id', 'item_id', string='Payment Items')
    jetcheckout_plan_ids = fields.Many2many('payment.plan', 'transaction_plan_rel', 'transaction_id', 'plan_id', string='Payment Plans')
    jetcheckout_webhook_ok = fields.Boolean('Webhook Notification', readonly=True)
    jetcheckout_webhook_state = fields.Boolean('Webhook Notification State', readonly=True)
    jetcheckout_webhook_state_message = fields.Text('Webhook Notification State Message', readonly=True)
    jetcheckout_webhook_failed_ids = fields.Many2many('payment.settings.notification.webhook', 'transaction_webhook_rel', 'transaction_id', 'webhook_id', string='Failed Webhook Notifications', readonly=True)
    jetcheckout_partner_user_id = fields.Many2one('res.users', 'Sales Representative', related='partner_id.user_id', store=True, readonly=True, ondelete='set null')
    jetcheckout_partner_team_id = fields.Many2one('crm.team', 'Sales Team', related='partner_id.team_id', store=True, readonly=True, ondelete='set null')
    jetcheckout_partner_categ_ids = fields.Many2many('res.partner.category', 'transaction_partner_category_rel', 'transaction_id', 'category_id', 'Tags', related='partner_id.category_id', store=True, readonly=True, ondelete='set null')

    def run_hook(self, subtype, **kwargs):
        company = self.company_id.root_id
        hooks = self.env['payment.hook'].sudo().search([
            ('type', '=', 'transaction'),
            ('subtype', '=', subtype),
            ('company_id', '=', company.id),
        ])
        for hook in hooks:
            hook.run(transaction=self, **kwargs)

    @api.model
    def create(self, values):
        if values.get('paylox_item_tag_id'):
            tag = self.env['payment.settings.campaign.tag'].sudo().browse(values['paylox_item_tag_id'])
            values['paylox_item_tag_name'] = tag.name
        if values.get('jetcheckout_item_ids'):
            item = self.env['payment.item'].sudo().browse(values['jetcheckout_item_ids'][0][2])
            values['paylox_item_tag_code'] = '/'.join(set([i.tag or '-' for i in item]))

        tx = super().create(values)

        if tx.system and tx.company_id.id != tx.partner_id.company_id.id:
            raise ValidationError(_('Payment and partner belong to different companies.'))

        tx.with_context(hook_next={'state': tx.state}).run_hook('transaction_create')

        if tx.partner_id.is_subpartner:
            partner = tx.company_id.partner_id
            tx.write({
                'partner_name': partner.name or partner.parent_id.name,
                'partner_vat': partner.vat,
                'partner_ref': partner.ref,
                'partner_lang': partner.lang,
                'partner_email': partner.email,
                'partner_zip': partner.zip,
                'partner_city': partner.city,
                'partner_state_id': partner.state_id.id,
                'partner_country_id': partner.country_id.id,
                'partner_phone': partner.mobile or partner.phone,
                'partner_address': payment_utils.format_partner_address(partner.street, partner.street2),
            })
        return tx

    def action_items(self):
        self.ensure_one()
        system = self.company_id.system or self.partner_id.system or 'jetcheckout_system'
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

    def action_export_txt(self):
        txs = self.filtered(lambda t: t.jetcheckout_can_export_txt)
        if not txs:
            raise UserError(_('You are not allowed to export transactions as TXT file. Please contact with your administrator.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/paylox/payment/transactions/txt?=%s' % ','.join(map(str, txs.ids))
        }

    @api.model
    def cron_export_txt(self):
        self = self.sudo()
        now = datetime.now()
        tz = timezone('Europe/Istanbul')
        now += tz.utcoffset(now)
        pre = now - timedelta(hours=1)
        companies = self.env['res.company'].search([
            ('system', '!=', False),
            ('payment_transaction_export_txt', '=', True),
            ('payment_transaction_export_txt_code', '!=', False),
            ('payment_transaction_export_txt_cron_ok', '=', True),
        ])
        for company in companies:
            try:
                days = map(lambda d: DAYS[d], company.payment_transaction_export_txt_cron_day_ids.mapped('code'))
                if now.weekday() in days:
                    hour = company.payment_transaction_export_txt_cron_hour % 24
                    time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                    if pre < time <= now:
                        today = now.replace(hour=0, minute=0, second=0, microsecond=0) + tz.utcoffset(now)
                        txt = self.export_txt([
                            ('create_date', '>=', today - timedelta(days=1)),
                            ('create_date', '<', today),
                            ('company_id', '=', company.id),
                            ('company_id.parent_id', '=', company.id),
                        ])
                        context = self.env.context.copy()
                        mail_server = company.mail_server_id
                        email_from = mail_server.email_formatted or company.email_formatted
                        context.update({'server': mail_server, 'from': email_from, 'company': company})
                        mail_template = self.env.ref('payment_jetcheckout_system.mail_template_export_txt')
                        for partner in company.payment_transaction_export_txt_cron_user_ids.mapped('partner_id'):
                            context.update({
                                'partner': partner,
                                'lang': partner.lang,
                                'receiver': partner.email_formatted,
                                'company': company,
                                'server': mail_server,
                                'sender': mail_server.email_formatted or company.email_formatted,
                                'domain': urlparse(self.get_base_url()).netloc,
                            })
                            try:
                                with self.env.cr.savepoint():
                                    mail_template.with_context(**context).send_mail(
                                        partner.id,
                                        force_send=True,
                                        email_values={
                                            'is_notification': True,
                                            'mail_server_id': mail_server.id,
                                            'attachments': [(
                                                txt.get('filename', ''),
                                                base64.b64encode(txt.get('content', '').encode('utf-8'))
                                            )]
                                        }
                                    )
                            except Exception as e:
                                _logger.error('An error occured when sending export txt email to %s: %s' % (partner.name, e))
                            self.env.cr.commit()
            except:
                _logger.error('An error occured when running export txt cron: %s' % e, exc_info=True)
                self.env.cr.rollback()

    def export_txt(self, domain=[]):
        if not domain:
            domain = [('id', 'in', self.ids)]

        domain += [
            ('state', '=', 'done'),
            ('jetcheckout_payment_type', 'in', ('virtual_pos', 'transfer')),
        ]

        transactions = self.env['payment.transaction'].sudo().search(domain, order='last_state_change desc')
        if not transactions:
            if self.env.user.share:
                raise MissingError(_('Transaction cannot be found.'))
            else:
                raise UserError(_('Transaction cannot be found.'))

        company = transactions.mapped('company_id.root_id')
        if len(company) > 1:
            raise ValidationError(_('You can export TXT of transactions only for one company at a time.'))
        if not company.payment_transaction_export_txt:
            raise ValidationError(_('Company "%s" is not allow to export TXT.') % company.name)
        if not company.payment_transaction_export_txt_code:
            raise ValidationError(_('Company "%s" does not have any TXT format code.') % company.name)

        context = {
            'txt': {},
            'env': self.env,
            'UserError': UserError,
            'datetime': _datetime,
            'logger': _logger,
            'json': _json,
            'pytz': _pytz,
            'company': company,
            'transactions': transactions,
            'formatter': formatLang,
        }
        try:
            safe_eval(company.payment_transaction_export_txt_code.strip(), context, mode='exec', nocopy=True)
            return context.get('txt', {})
        except UserError:
            raise
        except:
            _logger.error(traceback.format_exc())
            raise ValidationError(_('An error occured when getting TXT.'))

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

    def _paylox_auth_postprocess(self):
        prev_state = self.state
        res = super()._paylox_auth_postprocess()
        next_state = self.state
        self.with_context(hook_prev={'state': prev_state}, hook_next={'state': next_state}).run_hook('transaction_authorize')
        return res

    def _paylox_cancel_postprocess(self):
        prev_state = self.state
        res = super()._paylox_cancel_postprocess()
        next_state = self.state
        self.with_context(hook_prev={'state': prev_state}, hook_next={'state': next_state}).run_hook('transaction_cancel')
        return res

    def _paylox_done_postprocess(self):
        prev_state = self.state
        res = super()._paylox_done_postprocess()
        next_state = self.state
        self.with_context(hook_prev={'state': prev_state}, hook_next={'state': next_state}).run_hook('transaction_finalize')
        webhooks = self.company_id.notif_webhook_ids
        if webhooks:
            self.write({
                'jetcheckout_webhook_ok': True,
                'jetcheckout_webhook_failed_ids': [(6, 0, webhooks.ids)],
                'jetcheckout_webhook_state': True,
                'jetcheckout_webhook_state_message': _('This transaction has not been notified yet.')
            })
            self.action_process_notification_webhook()
        return res


class PaymentTransactionItem(models.Model):
    _name = 'payment.transaction.item'
    _description = 'Payment Transaction Items'

    transaction_id = fields.Many2one('payment.transaction', required=True, ondelete='cascade')
    item_id = fields.Many2one('payment.item', string='Item')
    ref = fields.Char('Reference')
    date = fields.Date('Date')
    desc = fields.Char('Description')
    advance = fields.Boolean('Advance')
    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one(related='transaction_id.currency_id')

    @api.model
    def create(self, values):
        res = super().create(values)
        if res.advance:
            res.transaction_id.paylox_prepayment_amount = res.amount
        return res
