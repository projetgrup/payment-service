# -*- coding: utf-8 -*-
import random
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class PartnerOtp(models.Model):
    _name = "res.partner.otp"
    _description = "OTP Authentication"

    def _compute_date(self):
        for otp in self:
            otp.date_local = fields.Datetime.context_timestamp(otp, otp.date).strftime(DATETIME_FORMAT)

    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, copy=False)
    code = fields.Char(string='Code', readonly=True, copy=False)
    date = fields.Datetime(string='Date', readonly=True, copy=False)
    date_local = fields.Char(compute='_compute_date')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False)
    lang = fields.Char(string='Language', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        if vals.get('partner_id'):
            code = random.random()
            vals.update({
                'code': str(code)[2:6],
                'date': fields.Datetime.now() + relativedelta(minutes=2)
            })
            res = super().create(vals)
            res.send_mail()
            res.send_sms()
            return res
        return

    @api.autovacuum
    def _gc_otp(self):
        domain = [('date', '<', fields.Datetime.now())]
        return self.sudo().search(domain).unlink()

    def send_mail(self):
        template = self.env.ref('payment_jetcheckout_system_otp.otp_mail_template')
        comment = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
        reply_to = self.env.user.email_formatted
        values = template.with_context(template_preview_lang=self.lang).generate_email(self.id, ['subject', 'body_html', 'email_from', 'reply_to', 'email_to', 'scheduled_date'])
        mail = self.env['mail.mail'].create({
            'message_type': 'comment',
            'subtype_id': comment,
            'res_id': self.partner_id.id,
            'recipient_ids': [(6, 0, (self.partner_id.id,))],
            'partner_ids': [(6, 0, (self.partner_id.id,))],
            'subject': values['subject'],
            'email_from': values['email_from'],
            'email_to': values['email_to'],
            'body': values['body'],
            'body_html': values['body'],
            'model': 'res.partner',
            'mail_server_id': values['mail_server_id'],
            'auto_delete': values['auto_delete'],
            'scheduled_date': values['scheduled_date'],
            'reply_to': reply_to,
            'state': 'outgoing',
            'is_notification': True,
            'notification_ids': [(0, 0, {
                'res_partner_id': self.partner_id.id,
                'notification_type': 'email',
            })]
        })
        mail.notification_ids.write({'mail_mail_id': mail.id})
        mail.with_context(lang=self.lang).send()

    def send_sms(self):
        phone = self.partner_id.mobile or self.partner_id.phone
        if phone:
            template = self.env.ref('payment_jetcheckout_system_otp.otp_sms_template')
            note = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
            provider_id = self.env['sms.provider'].get(self.company_id.id).id
            message = template._render_field('body', [self.id], set_lang=self.lang)[self.id]
            sms = self.env['sms.sms'].create({
                'partner_id': self.partner_id.id,
                'body': message,
                'number': phone,
                'state': 'outgoing',
                'provider_id': provider_id,
            })
            self.env['mail.message'].create({
                'res_id': self.partner_id.id,
                'model': 'res.partner',
                'message_type': 'sms',
                'subtype_id': note,
                'body': message,
                'notification_ids': [(0, 0, {
                    'res_partner_id': self.partner_id.id,
                    'sms_number': phone,
                    'notification_type': 'sms',
                    'sms_id': sms.id,
                    'is_read': True,
                    'notification_status': 'ready',
                    'failure_type': '',
                })]
            })
            sms.with_context(otp=True, no_exception=True)._send()
