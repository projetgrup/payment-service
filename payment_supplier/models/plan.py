# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PaymentPlan(models.Model):
    _inherit = 'payment.plan'

    def approve(self):
        super().approve()
        if not self.item_id.system_supplier_plan_mail_sent and \
           all(plan.approval_state == '+' for plan in self.item_id.plan_ids):

            try:
                with self.env.cr.savepoint():
                    company = self.item_id.company_id or self.env.company
                    template = self.env.ref('payment_supplier.mail_item_approved')
                    partner = self.partner_id
                    server = company.mail_server_id
                    amount = sum(self.item_id.plan_ids.mapped('amount_paid'))

                    context = self.env.context.copy()
                    context.update({
                        'amount': amount,
                        'company': company,
                        'server': server,
                        'tz': partner.tz,
                        'lang': partner.lang,
                        'currency': self.item_id.currency_id,
                        'from': server.email_formatted or company.email_formatted,
                    })

                    template.with_context(context).send_mail(
                        partner.id,
                        force_send=True,
                        email_values={
                            'is_notification': True,
                            'mail_server_id': server.id,
                        }
                    )
                    self.item_id.system_supplier_plan_mail_sent = True

            except Exception as e:
                _logger.error('Sending email for payment item #%s is failed\n%s' % (self.item_id.id, e))
 