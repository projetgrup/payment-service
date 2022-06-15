# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError

PRIMEFACTOR = 3367900313

class Partner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner','portal.mixin']

    def _compute_payment(self):
        for partner in self:
            if partner.parent_id:
                partner.payable_count = len(partner.parent_id.payment_ids)
                partner.paid_count = len(partner.parent_id.paid_ids)
            else:
                partner.payable_count = len(partner.payment_ids)
                partner.paid_count = len(partner.paid_ids)

    @api.onchange('parent_id')
    def _compute_sibling(self):
        for partner in self:
            if partner.parent_id:
                partner.sibling_ids = partner.parent_id.child_ids.filtered(lambda x: x.id != partner.id)
            else:
                partner.sibling_ids = False

    system = fields.Selection(related='company_id.system', store=True, readonly=True)
    payment_ids = fields.One2many('payment.item', 'parent_id', string='Payments', copy=False, domain=[('paid','=',False)])
    paid_ids = fields.One2many('payment.item', 'parent_id', string='Paid Items', copy=False, domain=[('paid','!=',False)])
    sibling_ids = fields.One2many('res.partner', compute='_compute_sibling')
    paid_count = fields.Integer(string='Items Paid', compute='_compute_payment')
    payable_count = fields.Integer(string='Items To Pay', compute='_compute_payment')
    date_email_sent = fields.Datetime('Email Sent Date', readonly=True)
    date_sms_sent = fields.Datetime('Sms Sent Date', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['company_id'] = self.env.company.id
        langs = self.env['res.lang'].get_installed()
        for lang in langs:
            if lang[0] == 'tr_TR':
                res['lang'] = 'tr_TR'
                break
        return res

    def _get_name(self):
        system = self.env.context.get('active_system') or self.env.context.get('system')
        if not system:
            return super()._get_name()

        partner = self
        return partner.name or ''

    def _get_token(self):
        return '%s-%x' % (self.access_token, self.id * PRIMEFACTOR)

    def _compute_access_url(self):
        for rec in self:
            rec.access_url = '/p/%s' % rec._get_token()

    def _get_share_url(self, redirect=False, signup_partner=False, pid=None):
        self.ensure_one()
        self._portal_ensure_token()
        return self.access_url

    def _get_payment_url(self, shorten=False):
        self.ensure_one()
        url = self.get_base_url() + self._get_share_url()
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

    def action_share_payment_link(self):
        self.ensure_one()
        return self.sudo().env.ref('payment_jetcheckout_system.payment_share').sudo().read()[0]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system = self.env.context.get('active_system') or self.env.context.get('system')
        if system:
            child = self.env.context.get('active_child', False)
            if child:
                if view_type == 'form':
                    view_id = self.env.ref('payment_%s.child_form' % system).id
                elif view_type == 'tree':
                    view_id = self.env.ref('payment_%s.child_tree' % system).id
            else:
                if view_type == 'form':
                    view_id = self.env.ref('payment_%s.parent_form' % system).id
                elif view_type == 'tree':
                    view_id = self.env.ref('payment_%s.parent_tree' % system).id
        return super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    def action_payable(self):
        self.ensure_one()
        system = self.company_id and self.company_id.system or self.env.context.get('active_system')
        action = self.env.ref('payment_%s.action_item' % system).sudo().read()[0]
        if self.parent_id:
            action['domain'] = [('child_id', '=', self.id)]
            action['context'] = {'default_child_id': self.id, 'search_default_filterby_payable': True, 'domain': self.ids}
        else:
            action['domain'] = [('parent_id', '=', self.id)]
            action['context'] = {'domain': self.child_ids.ids, 'search_default_filterby_payable': True}
        return action

    def action_paid(self):
        self.ensure_one()
        system = self.company_id and self.company_id.system or self.env.context.get('active_system')
        action = self.env.ref('payment_%s.action_item' % system).sudo().read()[0]
        if self.parent_id:
            action['domain'] = [('child_id', '=', self.id)]
            action['context'] = {'default_child_id': self.id, 'search_default_filterby_paid': True, 'domain': self.ids, 'create': False, 'edit': False, 'delete': False}
        else:
            action['domain'] = [('parent_id', '=', self.id)]
            action['context'] = {'domain': self.child_ids.ids, 'search_default_filterby_paid': True, 'create': False, 'edit': False, 'delete': False}
        return action

    def action_send(self):
        company = self.mapped('company_id')
        if not len(company) == 1:
            raise UserError(_('Partners have to be in one company when sending mass messages, but there are %s of them. (%s)') % (len(company), ', '.join(company.mapped('name'))))

        email = self.env.ref('payment_jetcheckout_system.send_type_email')
        mail_template = self.env['mail.template'].sudo().search([('company_id', '=',company.id)], limit=1)
        sms_template = self.env['sms.template'].sudo().search([('company_id', '=', company.id)], limit=1)
        res = self.env['payment.acquirer.jetcheckout.send'].create({
            'partner_ids': [(6, 0, self.ids)],
            'selection': [(6, 0, email.ids)],
            'type_ids': [(6, 0, email.ids)],
            'mail_template_id': mail_template.id,
            'sms_template_id': sms_template.id,
            'company_id': company.id,
        })
        action = self.env.ref('payment_jetcheckout_system.action_system_send').sudo().read()[0]
        action['res_id'] = res.id
        return action
