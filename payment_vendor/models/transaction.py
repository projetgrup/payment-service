# -*- coding: utf-8 -*-
import logging
import pytz
from datetime import datetime, timedelta
from itertools import groupby
from operator import itemgetter
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
                template.with_context(context).send_mail(partner.id, force_send=True, email_values={
                    'is_notification': True,
                    'mail_server_id': mail_server.id,
                })

        except Exception as e:
            self.env.cr.rollback()
            _logger.error('Sending email for transaction %s is failed\n%s' % (self.reference, e))

    @api.model
    def jetcheckout_send_daily_email(self):
        users = self.env.ref('payment_vendor.group_vendor_manager').mapped('users')
        template = self.env.ref('payment_vendor.mail_transaction_daily')
        now = datetime.now()

        for user in users:
            timezone = user[0].tz
            try:
                tz = pytz.timezone(timezone)
            except:
                tz = pytz.timezone('UTC')
            offset = tz.utcoffset(now)
            date_end = (now + offset).replace(hour=0, minute=0, second=0, microsecond=0)
            date_start = date_end - timedelta(days=1)

            for company in user.company_ids.filtered(lambda x: x.system == 'vendor'):
                websites = self.env['website'].sudo().search([('company_id', '=', company.id)])
                if not websites:
                    continue

                mail_server = company.mail_server_id
                context = self.env.context.copy()
                context['date'] = date_start.strftime('%d.%m.%Y')
                context['partner'] = user.partner_id
                context['company'] = company
                context['server'] = mail_server
                context['from'] = mail_server.email_formatted or company.email_formatted

                for website in websites:
                    context['url'] = website.domain
                    context['domain'] = urlparse(context['url']).netloc
                    context['transactions'] = []
                    context['total'] = 0

                    transactions = self.env['payment.transaction'].sudo().read_group([
                        ('company_id', '=', company.id),
                        ('last_state_change', '>=', date_start - offset),
                        ('last_state_change', '<', date_end - offset),
                        ('state', '=', 'done'),
                        ('jetcheckout_website_id', '=', website.id),
                    ], fields=['amount:sum'], groupby=['partner_id'], orderby='amount desc')
                    for transaction in transactions:
                        context['transactions'].append({'name': transaction['partner_id'][1], 'amount': transaction['amount']})
                        context['total'] += transaction['amount']

                    try:
                        template.with_context(context).send_mail(context['partner'].id, force_send=True, email_values={
                            'is_notification': True,
                            'mail_server_id': mail_server.id,
                        })
                    except Exception as e:
                        _logger.error('Sending daily email for partner %s is failed\n%s' % (context['partner'].name, e))
