# -*- coding: utf-8 -*-
import re
import logging
from datetime import date
from urllib.parse import urlparse
from collections import OrderedDict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import email_normalize
from .constants import PRIMEFACTOR

_logger = logging.getLogger(__name__)

EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PHONE_PATTERN = r'^[0-9]{10}$'

class PartnerTeam(models.Model):
    _inherit = 'crm.team'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('settings'):
            res['company_id'] = self.env.company.id
        return res


class PartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    company_id = fields.Many2one('res.company')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('settings'):
            res['company_id'] = self.env.company.id
        return res

class Partner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'portal.mixin']

    def _default_campaign_id(self):
        if self.env.company.payment_page_due_ok:
            return False
        return super()._default_campaign_id()

    def _compute_payment(self):
        for partner in self:
            domain_items = []
            domain_transactions = []
            if partner.parent_id:
                domain_items = [('child_id', '=', partner.id)]
                domain_transactions = [('partner_id', '=', partner.id)]
            else:
                domain_items = [('parent_id', '=', partner.id)]
                domain_transactions = [('partner_id', 'in', partner.child_ids.ids + [partner.id])]

            item_ids = self.env['payment.item'].search(domain_items)
            transaction_ids = self.env['payment.transaction'].search(domain_transactions)
            partner.payable_ids = item_ids.filtered(lambda x: x.paid == False)
            partner.paid_ids = item_ids.filtered(lambda x: x.paid != False)
            partner.transaction_failed_ids = transaction_ids.filtered(lambda x: x.state != 'done')
            partner.transaction_done_ids = transaction_ids.filtered(lambda x: x.state == 'done')
            partner.payable_count = len(partner.payable_ids)
            partner.paid_count = len(partner.paid_ids)
            partner.transaction_done_count = len(partner.transaction_done_ids)
            partner.transaction_failed_count = len(partner.transaction_failed_ids)

    def _search_payment(self, operator, operand):
        payables = self.env['payment.item'].search([('paid', '=', False)]).mapped('parent_id')
        if operator == '!=':
            return [('id', 'in', payables.ids)]
        if operator == '=':
            return [('id', 'not in', payables.ids)]
        return [('id', '=', 0)]

    @api.onchange('parent_id')
    def _compute_sibling(self):
        for partner in self:
            if partner.parent_id:
                partner.sibling_ids = partner.parent_id.child_ids.filtered(lambda x: x.id != partner.id)
            else:
                partner.sibling_ids = False

    @api.depends('user_ids', 'company_id')
    def _compute_user_details(self):
        for partner in self:
            users = partner.with_context(active_test=False).user_ids.filtered(lambda x: x.company_id.id == (partner.company_id.id or self.env.company.id))
            user = users[0] if users else False
            if user:
                partner.users_id = user.id
                if user.has_group('base.group_user'):
                    partner.is_internal = True
                    partner.is_portal = False
                elif user.has_group('base.group_portal'):
                    partner.is_internal = False
                    partner.is_portal = True
                else:
                    partner.is_internal = False
                    partner.is_portal = False
            else:
                partner.users_id = False
                partner.is_internal = False
                partner.is_portal = False

    def _compute_payment_link_url(self):
        for partner in self:
            partner.payment_link_url = partner._get_payment_url()

    def _compute_payment_page_url(self):
        for partner in self:
            partner.payment_page_url = partner.with_context(active_type='page')._get_payment_url()

    def _search_is_portal(self, operator, operand):
        group_portal = self.env.ref('base.group_portal')
        ids = group_portal.users.mapped('partner_id').ids
        operator = 1 if operator == '=' else -1
        operand = 1 if operand else -1
        op = 'in' if operator * operand == 1 else 'not in'
        return [('id', op, ids)]

    def _search_is_internal(self, operator, operand):
        group_user = self.env.ref('base.group_user')
        ids = group_user.users.mapped('partner_id').ids
        operator = 1 if operator == '=' else -1
        operand = 1 if operand else -1
        op = 'in' if operator * operand == 1 else 'not in'
        return [('id', op, ids)]

    system = fields.Selection(selection=[], readonly=True)
    payable_ids = fields.One2many('payment.item', string='Payable Items', copy=False, compute='_compute_payment', search='_search_payment', compute_sudo=True)
    paid_ids = fields.One2many('payment.item', string='Paid Items', copy=False, compute='_compute_payment', compute_sudo=True)
    transaction_done_ids = fields.One2many('payment.transaction', string='Done Transactions', copy=False, compute='_compute_payment', compute_sudo=True)
    transaction_failed_ids = fields.One2many('payment.transaction', string='Failed Transactions', copy=False, compute='_compute_payment', compute_sudo=True)
    sibling_ids = fields.One2many('res.partner', compute='_compute_sibling')
    paid_count = fields.Integer(string='Items Paid', compute='_compute_payment', compute_sudo=True)
    payable_count = fields.Integer(string='Items To Pay', compute='_compute_payment', compute_sudo=True)
    transaction_done_count = fields.Integer(string='Transaction Done', compute='_compute_payment', compute_sudo=True)
    transaction_failed_count = fields.Integer(string='Transaction Failed', compute='_compute_payment', compute_sudo=True)
    date_email_sent = fields.Datetime('Email Sent Date', readonly=True)
    date_sms_sent = fields.Datetime('Sms Sent Date', readonly=True)
    is_portal = fields.Boolean(compute='_compute_user_details', search='_search_is_portal', compute_sudo=True, readonly=True)
    is_internal = fields.Boolean(compute='_compute_user_details', search='_search_is_internal', compute_sudo=True, readonly=True)
    acquirer_branch_id = fields.Many2one('payment.acquirer.jetcheckout.branch', string='Payment Acquirer Branch')
    users_id = fields.Many2one('res.users', compute='_compute_user_details', compute_sudo=True, readonly=True)
    payment_link_url = fields.Char('Payment Link URL', compute='_compute_payment_link_url', compute_sudo=True, readonly=True)
    payment_page_url = fields.Char('Payment Page URL', compute='_compute_payment_page_url', compute_sudo=True, readonly=True)
    paylox_tax_office = fields.Char('Tax Office')

    @api.model
    def default_get(self, fields):
        if not self.env.su and self.env.user.company_id.system and not self.env.user.has_group('payment_jetcheckout_system.group_system_create_partner'):
            raise UserError(_('You do not have permission to create a partner'))
 
        res = super().default_get(fields)
        if not self.env.context.get('skip_company') and self.env.company.system:
            res['company_id'] = self.env.company.id
        langs = self.env['res.lang'].get_installed()
        for lang in langs:
            if lang[0] == 'tr_TR':
                res['lang'] = 'tr_TR'
                break
        return res

    @api.model
    def create(self, values):
        if not self.env.su and self.env.user.company_id.system and not self.env.user.has_group('payment_jetcheckout_system.group_system_create_partner'):
            raise UserError(_('You do not have permission to create a partner'))

        if 'system' not in values and 'company_id' in values:
            company = self.env['res.company'].sudo().browse(values['company_id'])
            if company and company.system:
                values['system'] = company.system

        if 'is_company' not in values:
            values['is_company'] = True

        res = super().create(values)

        if 'user_id' in values:
            if values['user_id']:
                pid = self.env['res.users'].browse(values['user_id']).partner_id.id
                res.message_subscribe([pid])

        return res

    def write(self, values):
        if 'system' not in values and 'company_id' in values:
            company = self.env['res.company'].sudo().browse(values['company_id'])
            if company and company.system:
                values['system'] = company.system

        if 'user_id' in values:
            users = []
            for partner in self:
                users.append((partner, partner.user_id.id))

        res = super().write(values)

        if 'user_id' in values:
            for partner, uid in users:
                if not values['user_id'] == uid:
                    if uid:
                        pid = self.env['res.users'].browse(uid).partner_id.id
                        partner.message_unsubscribe([pid])
                    if values['user_id']:
                        pid = self.env['res.users'].browse(values['user_id']).partner_id.id
                        partner.message_subscribe([pid])

        return res

    def _get_name(self):
        system = self.env.context.get('active_system') or self.env.context.get('system')
        if not system:
            return super()._get_name()

        partner = self
        return partner.name or ''

    def _get_token(self):
        self._portal_ensure_token()
        return '%s-%x' % (self.access_token, self.id * PRIMEFACTOR)

    def _get_companies(self):
        return self.search([('vat', '!=', False), ('vat', '=', self.vat)]).mapped('company_id')

    def _get_tags(self):
        return self.search([('vat', '!=', False), ('vat', '=', self.vat), ('company_id', '=', self.env.company.id)]).mapped('category_id')

    def _get_payments(self):
        tags = OrderedDict()
        date_empty = date(1, 1, 1)
        company = self.env.company

        payment_tag = self.env['payment.settings.campaign.tag'].sudo().search([
            ('company_id', '=', company.id),
            ('campaign_id', '=', False)
        ], limit=1)
        payments = self.payable_ids
        for payment in payments:
            if not payment.tag:
                if payment_tag:
                    if payment_tag.id not in tags:
                        tags[payment_tag.id] = []
                    tags[payment_tag.id].append(payment.id)
            else:
                tag = self.env['payment.settings.campaign.tag.line'].sudo().search([
                    ('campaign_id.company_id', '=', company.id),
                    ('name', '=', payment.tag)
                ])
                if tag:
                    for t in tag:
                        if t.campaign_id.id not in tags:
                            tags[t.campaign_id.id] = []
                        tags[t.campaign_id.id].append(payment.id)
                else:
                    if payment_tag:
                        if payment_tag.id not in tags:
                            tags[payment_tag.id] = []
                        tags[payment_tag.id].append(payment.id)

        payments_tag = []
        if tags:
            keys = list(tags.keys())
            payments_tag = self.env['payment.settings.campaign.tag'].sudo().browse(keys).sorted(lambda x: x.campaign_id)
            payments = self.env['payment.item'].sudo().browse(tags[payments_tag[0].id]).sorted(lambda x: x.date or date_empty)
        else:
            payments = payments.sorted(lambda x: x.date or date_empty)
        return payments, payments_tag

    @api.model
    def _resolve_token(self, token):
        try:
            data = token.rsplit('-', 1)
            token = data[0]
            id = int(int(data[1], 16) / PRIMEFACTOR)
            return id, token
        except:
            return False

    @api.depends_context('active_type')
    def _compute_access_url(self):
        type = self.env.context.get('active_type')
        if type == 'page':
            prefix = '/my/payment'
        else:
            prefix = '/p'

        for rec in self:
            rec.access_url = '%s/%s' % (prefix, rec._get_token())

    def _get_share_url(self, **kwargs):
        self.ensure_one()
        self._portal_ensure_token()
        return self.access_url

    def _get_payment_url(self, shorten=False):
        self.ensure_one()
        base_url = self.get_base_url() or ''
        share_url = self._get_share_url() or ''
        url = base_url + share_url
        if shorten:
            link = self.env['link.tracker'].sudo().search_or_create({
                'url': url,
                'title': self.name,
            })
            url = link.short_url
        return url

    def _get_payment_company(self):
        self.ensure_one()
        return self.company_id and self.company_id.name or self.env.company.name

    def action_grant_access(self):
        self.ensure_one()
        self._check_portal_user()

        if self.is_portal or self.is_internal:
            raise UserError(_('The partner "%s" already has the portal access.', self.partner_id.name))

        self_sudo = self.sudo()
        group_portal = self_sudo.env.ref('base.group_portal')
        group_public = self_sudo.env.ref('base.group_public')

        user = self.users_id

        if not user:
            company = self.company_id or self.env.company
            user = self_sudo.with_company(company.id)._create_portal_user()

        user = user.sudo()
        if not user.active or user.has_group('base.group_public'):
            user.write({'active': True, 'groups_id': [(4, group_portal.id), (3, group_public.id)]})
            self_sudo.signup_prepare()

        self_sudo.with_context(active_test=True)._send_portal_email()
        return True

    def action_revoke_access(self):
        self.ensure_one()

        if not self.is_portal:
            raise UserError(_('The partner "%s" has no portal access.', self.name))

        self_sudo = self.sudo()
        group_portal = self_sudo.env.ref('base.group_portal')
        group_public = self_sudo.env.ref('base.group_public')
        self_sudo.signup_token = False

        user = self.users_id
        if not user:
            return True

        user.sudo().write({'groups_id': [(3, group_portal.id), (4, group_public.id)], 'active': False})
        return True

    def action_invite_again(self):
        self.ensure_one()
        if not self.is_portal:
            raise UserError(_('You should first grant the portal access to the partner "%s".', self.name))
        self_sudo = self.sudo()
        self_sudo.with_context(active_test=True)._send_portal_email()

    def _check_portal_user(self):
        self.ensure_one()
        email = email_normalize(self.email)
        if not email:
            raise UserError(_('The contact "%s" does not have a valid email.', self.name))

        user = self.env['res.users'].sudo().with_context(active_test=False).search([
            ('id', '!=', self.users_id.id),
            ('login', '=', email),
        ])

        if user:
            raise UserError(_('The contact "%s" has the same email has an existing user (%s).', self.name, user.name))

    def _create_portal_user(self):
        return self.env['res.users'].with_context(no_reset_password=True)._create_user_from_template({
            'email': email_normalize(self.email),
            'login': email_normalize(self.email),
            'partner_id': self.id,
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, self.env.company.ids)],
        })

    def _send_portal_email(self):
        self.ensure_one()
        template = self.env.ref('payment_jetcheckout_system.portal_mail_template')
        if not template:
            raise UserError(_('The template "Portal: new user" not found for sending email to the portal user.'))

        lang = self.lang
        portal_url = self.with_context(signup_force_type_in_url='', lang=lang)._get_signup_url_for_action()[self.id]
        self.signup_prepare()

        template.with_context(dbname=self._cr.dbname, portal_url=portal_url, lang=lang).send_mail(self.id, force_send=True)
        return True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system = self.env.context.get('active_system') or self.env.context.get('system')
        subsystem = self.env.context.get('active_subsystem') or self.env.context.get('subsystem')
        if system:
            if subsystem:
                subsystem = subsystem.replace('%s_' % system, '') + '_'
            else:
                subsystem = ''

            child = self.env.context.get('active_child', False)
            if child:
                if view_type == 'form':
                    try:
                        view_id = self.env.ref('payment_%s.%schild_form' % (system, subsystem)).id
                    except:
                        view_id = self.env.ref('payment_%s.child_form' % (system,)).id
                elif view_type == 'tree':
                    try:
                        view_id = self.env.ref('payment_%s.%schild_tree' % (system, subsystem)).id
                    except:
                        view_id = self.env.ref('payment_%s.child_tree' % (system,)).id
            else:
                if view_type == 'form':
                    try:
                        view_id = self.env.ref('payment_%s.%sparent_form' % (system, subsystem)).id
                    except:
                        view_id = self.env.ref('payment_%s.parent_form' % (system,)).id
                elif view_type == 'tree':
                    try:
                        view_id = self.env.ref('payment_%s.%sparent_tree' % (system, subsystem)).id
                    except:
                        view_id = self.env.ref('payment_%s.parent_tree' % (system,)).id
        return super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    def action_payable(self):
        self.ensure_one()
        system = self.company_id and self.company_id.system or self.system or self.env.context.get('active_system') or 'jetcheckout_system'
        action = self.env.ref('payment_%s.action_item' % system).sudo().read()[0]
        action['domain'] = [('id', 'in', self.payable_ids.ids)]
        if self.parent_id:
            action['context'] = {'default_child_id': self.id, 'search_default_filterby_payable': True, 'domain': self.ids}
        else:
            action['context'] = {'domain': self.child_ids.ids, 'search_default_filterby_payable': True}
        return action

    def action_paid(self):
        self.ensure_one()
        system = self.company_id and self.company_id.system or self.system or self.env.context.get('active_system') or 'jetcheckout_system'
        action = self.env.ref('payment_%s.action_item' % system).sudo().read()[0]
        action['domain'] = [('id', 'in', self.paid_ids.ids)]
        if self.parent_id:
            action['context'] = {'default_child_id': self.id, 'search_default_filterby_paid': True, 'domain': self.ids, 'create': False, 'edit': False, 'delete': False}
        else:
            action['context'] = {'domain': self.child_ids.ids, 'search_default_filterby_paid': True, 'create': False, 'edit': False, 'delete': False}
        return action

    def action_transaction_done(self):
        self.ensure_one()
        action = self.env.ref('payment_jetcheckout_system.action_transaction').sudo().read()[0]
        action['domain'] = [('id', 'in', self.transaction_done_ids.ids)]
        return action

    def action_transaction_failed(self):
        self.ensure_one()
        action = self.env.ref('payment_jetcheckout_system.action_transaction').sudo().read()[0]
        action['domain'] = [('id', 'in', self.transaction_failed_ids.ids)]
        return action

    def action_share_link(self):
        action = self.env["ir.actions.actions"]._for_xml_id("portal.portal_share_action")
        action['context'] = {
            'active_id': self.env.context['active_id'],
            'active_model': self.env.context['active_model'],
            'active_type': 'link',
            'company': self.company_id.id or self.env.company.id,
        }
        return action

    def action_share_page(self):
        action = self.env["ir.actions.actions"]._for_xml_id("portal.portal_share_action")
        action['context'] = {
            'active_id': self.env.context['active_id'],
            'active_model': self.env.context['active_model'],
            'active_type': 'page',
            'company': self.company_id.id or self.env.company.id,
        }
        return action

    def action_share_payment_link(self):
        self.ensure_one()
        return self.sudo().env.ref('payment_jetcheckout_system.payment_share_link').sudo().read()[0]

    def action_share_payment_page(self):
        self.ensure_one()
        return self.sudo().env.ref('payment_jetcheckout_system.payment_share_page').sudo().read()[0]

    def action_redirect_payment_link(self):
        self.ensure_one()
        wizard = self.env['payment.item.wizard'].create({
            'partner_id': self.id,
            'url': self._get_payment_url(),
        })
        action = self.sudo().env.ref('payment_jetcheckout_system.action_item_wizard').sudo().read()[0]
        action['res_id'] = wizard.id
        return action

    def action_redirect_payment_page(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '%s/my/payment/%s' % (self.get_base_url(), self._get_token())
        }

    def action_send(self):
        company = self.mapped('company_id') or self.env.company
        if len(company) > 1:
            raise UserError(_('Partners have to be in one company when sending mass messages, but there are %s of them. (%s)') % (len(company), ', '.join(company.mapped('name'))))

        params = self.env['ir.config_parameter'].sudo().get_param
        mail_template = self.env['mail.template'].sudo().search([('company_id', '=',company.id)], limit=1)
        if not mail_template and params('paylox.email.default'):
            id = int(params('paylox.email.template', '0'))
            mail_template = self.env['mail.template'].browse(id)
        sms_template = self.env['sms.template'].sudo().search([('company_id', '=', company.id)], limit=1)
        if not sms_template and params('paylox.sms.default'):
            id = int(params('paylox.sms.template', '0'))
            sms_template = self.env['sms.template'].browse(id)
 
        type_email = self.env.ref('payment_jetcheckout_system.send_type_email')
        res = self.env['payment.acquirer.jetcheckout.send'].create({
            'selection': [(6, 0, type_email.ids)],
            'type_ids': [(6, 0, type_email.ids)],
            'mail_template_id': mail_template.id,
            'sms_template_id': sms_template.id,
            'company_id': company.id,
        })
        action = self.env.ref('payment_jetcheckout_system.action_system_send').sudo().read()[0]
        action['res_id'] = res.id
        action['context'] = {
            'readonly': True,
            'active_ids': self.ids,
            'active_model': 'res.partner'
        }
        return action

    def action_follower(self):
        action = self.env.ref('payment_jetcheckout_system.action_partner_follower').sudo().read()[0]
        action['context'] = {'default_company_id': self.env.company.id}
        return action

    def action_follow(self):
        pid = self.env.user.partner_id.id
        for partner in self:
            partner.message_subscribe([pid])

    def action_unfollow(self):
        pid = self.env.user.partner_id.id
        for partner in self:
            partner.message_unsubscribe([pid])

    @api.model
    def send_payment_link(self, type, link, lang, value):
        if type == 'email':
            if (not re.match(EMAIL_PATTERN, value)):
                return {'error': _('Email address is not valid.')}

            try:
                company = self.env.company
                template = self.env.ref('payment_jetcheckout_system.mail_template_payment_link_share')
                server = company.mail_server_id

                context = self.env.context.copy()
                context.update({
                    'domain': urlparse(link).netloc,
                    'sender': server.email_formatted or company.email_formatted,
                    'receiver': value,
                    'company': company,
                    'link': link,
                    'lang': lang,
                    'server': server,
                })
                template.with_context(context).send_mail(self.env.user.partner_id.id, force_send=True, email_values={
                    'mail_server_id': server.id,
                })
                return {'message': _('Email has been sent successfully.')}
            except Exception as e:
                _logger.error('Sending email for payment link is failed\n%s' % e)
                return {'error': _('Email could not be sent.')}

        elif type == 'sms':
            if (not re.match(PHONE_PATTERN, value)):
                return {'error': _('Phone number is not valid.')}

            try:
                company = self.company_id or self.env.company
                template = self.env.ref('payment_jetcheckout_system.sms_template_payment_link_share')
                params = self.env['ir.config_parameter'].sudo().get_param
                provider = self.env['sms.provider'].get(company.id)
                if not provider and params('paylox.sms.default'):
                    id = int(params('paylox.sms.provider', '0'))
                    provider = self.env['sms.provider'].browse(id)

                context = self.env.context.copy()
                context.update({
                    'domain': urlparse(link).netloc,
                    'company': company,
                    'link': link,
                    'lang': lang,
                })

                body = template.with_context(context)._render_field('body', [self.env.user.partner_id.id], set_lang=self.env.context.get('lang'))[self.env.user.partner_id.id]
                sms = self.env['sms.sms'].create({
                    'partner_id': self.env.user.partner_id.id,
                    'body': body,
                    'number': value,
                    'state': 'outgoing',
                    'provider_id': provider.id,
                })
                sms.send()
                return {'message': _('SMS has been sent successfully.')}

            except Exception as e:
                _logger.error('Sending sms for payment link is failed\n%s' % e)
                return {'error': _('SMS could not be sent.')}

        return {'error': _('Unknown sending method')}