# -*- coding: utf-8 -*-
import logging
import pytz
from datetime import datetime
from urllib.parse import urlparse
from odoo import models, api

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _jetcheckout_done_postprocess(self):
        super()._jetcheckout_done_postprocess()
        self.jetcheckout_send_done_email()

    def jetcheckout_send_done_email(self):
        self.ensure_one()
        try:
            self.env.cr.commit()
            template = self.env.ref('payment_vendor.mail_transaction_successful')
            partner = self.partner_id
            commercial_partner = partner.commercial_partner_id
            followers = self.env['mail.followers'].search([('res_model', '=', 'res.partner'), ('res_id', '=', commercial_partner.id)])
            partners = followers.mapped('partner_id') | partner
            company = self.env.company
            mail_server = company.mail_server_id

            context = self.env.context.copy()
            context['tx'] = self
            context['partner'] = commercial_partner
            context['company'] = company
            context['server'] = mail_server
            context['url'] = self.jetcheckout_website_id.domain
            context['domain'] = urlparse(context['url']).netloc
            context['from'] = mail_server.email_formatted or company.email_formatted

            for partner in partners:
                template.with_context(context).send_mail(partner.id, force_send=True, email_values={'mail_server_id': mail_server.id})

        except Exception as e:
            self.env.cr.rollback()
            _logger.error('Sending email for transaction %s is failed\n%s' % (self.reference, e))

    @api.model
    def jetcheckout_send_daily_email(self):
        websites = self.env['website'].sudo().search([])
        template = self.env.ref('payment_vendor.mail_transaction_daily')
        users = self.env.ref('payment_vendor.group_vendor_manager').mapped('users')
        now = datetime.now()

        for website in websites:
            company = website.company_id
            if not company.system == 'vendor':
                continue

            user = users.filtered(lambda x: x.company_id.id == company.id)
            if not user:
                continue

            txs = {}
            mail_server = company.mail_server_id
            timezone = user[0].tz
            try:
                tz = pytz.timezone(timezone)
            except:
                tz = pytz.timezone('UTC')
            offset = tz.utcoffset(now)
            date_start = (now + offset).replace(hour=0, minute=0, second=0, microsecond=0) - offset
            date_end = (now + offset).replace(hour=0, minute=0, second=0, microsecond=0) - offset

            context = self.env.context.copy()
            context['date'] = date_start.strftime('%d.%m.%Y')
            context['partner'] = company.partner_id
            context['company'] = company
            context['server'] = mail_server
            context['url'] = website.domain
            context['domain'] = urlparse(context['url']).netloc
            context['from'] = mail_server.email_formatted or company.email_formatted

            transactions = self.env['payment.transaction'].sudo().search([
                ('company_id', '=', company.id),
                ('last_state_change', '>=',  '2022-01-01 00:00:00'),
                ('last_state_change', '<',  date_end),
            ])
            for transaction in transactions:
                pid = transaction.partner_id.id
                amount_new = transaction.jetcheckout_payment_amount

                if pid not in txs:
                    name = transaction.partner_id.name
                    txs[pid] = {'name': name, 'amount': 0}

                amount_now = txs[pid]['amount']
                amount_total = amount_now + amount_new
                txs[pid]['amount'] = amount_total

            context['transactions'] = txs.items()
            context['total'] = 0
            for key, value in context['transactions']:
                context['total'] += value['amount']

            try:
                template.with_context(context).send_mail(context['partner'].id, force_send=True, email_values={'mail_server_id': mail_server.id})
            except Exception as e:
                _logger.error('Sending daily email for partner %s is failed\n%s' % (context['partner'].name, e))
