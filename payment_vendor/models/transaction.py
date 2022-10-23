# -*- coding: utf-8 -*-
import logging
from odoo import models
from urllib.parse import urlparse

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
            template = self.env.ref('payment_vendor.mail_successful_transaction')
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
