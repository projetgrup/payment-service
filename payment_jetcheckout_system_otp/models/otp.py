# -*- coding: utf-8 -*-
import random
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class PartnerOtp(models.Model):
    _name = "res.partner.otp"
    _description = "OTP Authentication"

    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, copy=False)
    code = fields.Integer(string='Code', readonly=True, copy=False)
    date = fields.Datetime(string='Date', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False)
    lang = fields.Char(string='Language', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        if vals.get('partner_id'):
            code = random.random()
            vals.update({
                'code': int(code * 1000000),
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
        template.with_context(lang=self.lang).send_mail(self.id, force_send=True)

    def send_sms(self):
        template = self.env.ref('payment_jetcheckout_system_otp.otp_sms_template')
        message = template._render_field('body', [self.id], set_lang=self.lang)[self.id]
        self.env['sms.api'].with_context(otp=True, no_exception=True)._send_sms(self.partner_id.mobile or self.partner_id.phone, message)
