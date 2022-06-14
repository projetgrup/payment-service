# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import json

class PaymentAcquirerJetcheckoutSendType(models.Model):
    _name = 'payment.acquirer.jetcheckout.send.type'
    _description = 'Jetcheckout System Send Types'
    _order = 'sequence'
    _mail_fields = {
        'subject': 'mail_subject',
        'body_html': 'mail_body',
        'email_from': 'mail_from',
        'email_to': 'mail_to',
        'email_cc': 'mail_cc',
        'reply_to': 'mail_reply_to',
    }
    
    @api.model
    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    @api.model
    def _selection_languages(self):
        return self.env['res.lang'].get_installed()

    def _compute_icon(self):
        for type in self:
            if type.icon:
                type.icon_preview = '<i class="fa ' + type.icon + '"></i>'
            else:
                type.icon_preview = ''

    def _compute_message(self):
        for type in self:
            message = ''
            if type.code == 'email':
                server = self.env['ir.mail_server'].sudo().search([('company_id', '=', type.company_id.id)], limit=1)
                if server:
                    message = _('Emails are going to be sent on %s') % server.smtp_host
                else:
                    message = _('There is not any outgoing mail server set')
            elif type.code == 'sms':
                provider = getattr(type.company_id, 'sms_provider')
                if provider:
                    message = _('SMS messages are going to be sent on %s') % provider.capitalize()
                else:
                    message = _('There is not any SMS provider selected')
            else:
                message = _('This feature is implemented soon')

            type.message = message

    def _compute_params(self):
        for type in self:
            type.company_id = self.env.context.get('company_id')
            type.partner_ids = self.env.context.get('partner_ids')

    def _compute_template(self):
        parent = self.env['payment.acquirer.jetcheckout.send'].browse(self.env.context.get('parent', 0))
        for type in self:
            if type.code == 'email':
                type.mail_template_id = parent.mail_template_id.id
                type.template_name = parent.mail_template_id.name
                type.sms_template_id = False
            elif type.code == 'sms':
                type.sms_template_id = parent.sms_template_id.id
                type.template_name = parent.sms_template_id.name
                type.mail_template_id = False
            else:
                type.template_name = 'Empty'
                type.mail_template_id = False
                type.sms_template_id = False

    def _set_template(self):
        parent = self.env['payment.acquirer.jetcheckout.send'].browse(self.env.context.get('parent', 0))
        for type in self:
            if type.code == 'email':
                parent.mail_template_id = type.mail_template_id.id
            elif type.code == 'sms':
                parent.sms_template_id = type.sms_template_id.id

    def _set_mail_attributes(self, values=None):
        for key, val in self._mail_fields.items():
            field_value = values.get(key, False) if values else self.mail_template_id[key]
            self[val] = field_value

    @api.onchange('mail_template_id', 'partner_id', 'lang')
    def _compute_mail_fields(self):
        for type in self:
            try:
                if type.mail_template_id:
                    template = type.mail_template_id.with_context(lang=type.lang)
                    if self.partner_id:
                        values = template.with_context(template_preview_lang=type.lang).generate_email(type.partner_id.id, self._mail_fields.keys())
                        type._set_mail_attributes(values=values)
                    else:
                        type._set_mail_attributes()
                else:
                    type._set_mail_attributes()

            except Exception as e:
                error = str(e)
                if '\n' in error:
                    error = error.split('\n')[0]
                if ' : ' in error:
                    error = error.split(' : ')[1]
                raise UserError(error)

    @api.onchange('sms_template_id', 'partner_id', 'lang')
    def _compute_sms_fields(self):
        for type in self:
            try:
                if type.sms_template_id:
                    if type.partner_id:
                        type.sms_body = type.sms_template_id._render_field('body', [type.partner_id.id], set_lang=type.lang)[type.partner_id.id]
                    else:
                        type.sms_body = type.sms_template_id.body
                else:
                    type.sms_body = type.sms_template_id.body

            except Exception as e:
                error = str(e)
                if '\n' in error:
                    error = error.split('\n')[0]
                if ' : ' in error:
                    error = error.split(' : ')[1]
                raise UserError(error)

    name = fields.Char(required=True, readonly=True, translate=True)
    code = fields.Char(required=True, readonly=True)
    sequence = fields.Integer(default=16)
    icon = fields.Char()

    icon_preview = fields.Html(compute='_compute_icon', sanitize=False, compute_sudo=True)
    message = fields.Char(compute='_compute_message', compute_sudo=True)
    company_id = fields.Many2one('res.company', compute='_compute_params', compute_sudo=True)
    partner_ids = fields.Many2many('res.partner', compute='_compute_params', compute_sudo=True)
    partner_id = fields.Many2one('res.partner', string='Partner', store=False, default=False)
    lang = fields.Selection(_selection_languages, string='Language', store=False)
    template_name = fields.Char(compute='_compute_template', compute_sudo=True)

    mail_template_id = fields.Many2one('mail.template', string='Email Template', compute='_compute_template', inverse='_set_template', readonly=False, compute_sudo=True)
    mail_subject = fields.Char(compute='_compute_mail_fields', compute_sudo=True)
    mail_from = fields.Char(compute='_compute_mail_fields', compute_sudo=True)
    mail_to = fields.Char(compute='_compute_mail_fields', compute_sudo=True)
    mail_cc = fields.Char(compute='_compute_mail_fields', compute_sudo=True)
    mail_reply_to = fields.Char(compute='_compute_mail_fields', compute_sudo=True)
    mail_body = fields.Html(sanitize=False, compute='_compute_mail_fields', compute_sudo=True)

    sms_template_id = fields.Many2one('sms.template', string='Sms Template', compute='_compute_template', inverse='_set_template', readonly=False, compute_sudo=True)
    sms_body = fields.Text(compute='_compute_sms_fields', compute_sudo=True)

    @api.model
    def create(self, vals):
        if self.env.context.get('readonly'):
            return False
        return super().create(vals)

    def write(self, vals):
        if self.env.context.get('readonly'):
            return False
        return super().write(vals)

    def unlink(self):
        if self.env.context.get('readonly'):
            return False
        return super().unlink()


class PaymentAcquirerJetcheckoutSend(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.send'
    _description = 'Jetcheckout System Send'

    def _compute_partner(self):
        for send in self:
            send.partner_ids = [(6, 0, self.env.context.get('active_ids', []))]
            send.partner_count = len(send.partner_ids)

    partner_ids = fields.Many2many('res.partner', compute='_compute_partner', string='Partners')
    partner_count = fields.Integer(compute='_compute_partner')
    selection = fields.Many2many('payment.acquirer.jetcheckout.send.type', 'system_send_type_rel', 'send_id', 'type_id', string='Selection')
    type_ids = fields.Many2many('payment.acquirer.jetcheckout.send.type', 'system_send_type_rel', 'send_id', 'type_id', string='Types')
    mail_template_id = fields.Many2one('mail.template')
    sms_template_id = fields.Many2one('sms.template')
    company_id = fields.Many2one('res.company')

    @api.onchange('selection')
    def onchange_selection(self):
        self.type_ids = self.selection

    def send(self):
        self = self.sudo()
        selections = self.selection.mapped('code')
        mail_template = 'email' in selections and self.mail_template_id or False
        sms_template = 'sms' in selections and self.sms_template_id or False
        comment = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
        note = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
        reply_to = self.env.user.email_formatted
        mail_messages = []
        sms_messages = []


        for partner in self.partner_ids:
            if mail_template:
                values = mail_template.with_context(template_preview_lang=partner.lang).generate_email(partner.id, ['subject', 'body_html', 'email_from', 'reply_to', 'email_to', 'scheduled_date'])
                mail_values = {
                    'message_type': 'comment',
                    'subtype_id': comment,
                    'res_id': values['res_id'],
                    'recipient_ids': [(6, 0, (values['res_id'],))],
                    'partner_ids': [(6, 0, (values['res_id'],))],
                    'subject': values['subject'],
                    'email_from': values['email_from'],
                    'email_to': values['email_to'],
                    'body': values['body'],
                    'body_html': values['body'],
                    'model': values['model'],
                    'mail_server_id': values['mail_server_id'],
                    'auto_delete': values['auto_delete'],
                    'scheduled_date': values['scheduled_date'],
                    'reply_to': reply_to,
                    'state': 'outgoing',
                    'is_notification': True,
                    'notification_ids': [(0, 0, {
                        'res_partner_id': values['res_id'],
                        'notification_type': 'email',
                    })]
                }
                mail_messages.append(mail_values)

            if sms_template:
                body = sms_template._render_field('body', [partner.id], set_lang=partner.lang)[partner.id]
                sms_values = {
                    'partner_id': partner.id,
                    'body': body,
                    'number': partner.mobile,
                    'state': 'outgoing',
                }
                sms_messages.append(sms_values)

        if mail_messages or sms_messages:
            sent_values = {}
            now = fields.Datetime.now()
            if mail_messages:
                sendings = self.env['mail.mail'].create(mail_messages)
                for sending in sendings:
                    sending.notification_ids.write({'mail_mail_id': sending.id})
                self.env.ref('mail.ir_cron_mail_scheduler_action')._trigger()
                sent_values['date_email_sent'] = now
            if sms_messages:
                sendings = self.env['sms.sms'].create(sms_messages)
                messages = []
                for sending in sendings:
                    messages.append({
                        'res_id': sending.partner_id.id,
                        'model': 'res.partner',
                        'message_type': 'sms',
                        'subtype_id': note,
                        'body': sending.body,
                        'notification_ids': [(0, 0, {
                            'res_partner_id': sending.partner_id.id,
                            'sms_number': sending.number,
                            'notification_type': 'sms',
                            'sms_id': sending.id,
                            'is_read': True,
                            'notification_status': 'ready' if sending.state == 'outgoing' else 'exception',
                            'failure_type': '' if sending.state == 'outgoing' else sending.failure_type,
                        })]
                    })
                self.env['mail.message'].create(messages)
                self.env.ref('sms.ir_cron_sms_scheduler_action')._trigger()
                sent_values['date_sms_sent'] = now
            self.partner_ids.write(sent_values)
