# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.http import request

class PaymentAcquirerJetcheckoutTerms(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.term'
    _description = 'Jetcheckout Terms'

    company_id = fields.Many2one('res.company')
    partner_id = fields.Many2one('res.partner')
    domain = fields.Char()

class PaymentAcquirerJetcheckoutStatus(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.status'
    _description = 'Jetcheckout Status'

    transaction_date = fields.Datetime(readonly=True)
    vpos_id = fields.Char(readonly=True)
    is_successful = fields.Boolean(readonly=True)
    is_completed = fields.Boolean(readonly=True)
    is_cancelled = fields.Boolean(readonly=True)
    is_3d = fields.Boolean(readonly=True)
    currency_id =fields.Many2one('res.currency', readonly=True)
    amount = fields.Monetary(readonly=True)
    commission = fields.Monetary(readonly=True)
    cost_rate = fields.Float(readonly=True)
    auth_code = fields.Char(readonly=True)
    service_ref_id = fields.Char(readonly=True)

class PaymentAcquirerJetcheckoutRefund(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.refund'
    _description = 'Jetcheckout Refund'

    transaction_id =fields.Many2one('payment.transaction', readonly=True)
    currency_id =fields.Many2one('res.currency', readonly=True)
    total = fields.Monetary(readonly=True)
    amount = fields.Monetary()

    def confirm(self):
        if self.amount > self.total:
            raise UserError(_('Refund amount cannot be higher than total amount'))
        self.transaction_id.jetcheckout_s2s_do_refund(amount=self.amount)
        return {'type': 'ir.actions.act_window_close'}

class PaymentAcquirerJetcheckoutProvider(models.Model):
    _name = 'payment.acquirer.jetcheckout.provider'
    _description = 'Jetcheckout Provider'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)

class PaymentAcquirerJetcheckoutPos(models.Model):
    _name = 'payment.acquirer.jetcheckout.pos'
    _description = 'Jetcheckout Pos'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    provider_id = fields.Many2one('payment.acquirer.jetcheckout.provider', required=True)

class PaymentAcquirerJetcheckoutBank(models.Model):
    _name = 'payment.acquirer.jetcheckout.bank'
    _description = 'Jetcheckout Bank'
    _order = 'sequence'

    acquirer_id = fields.Many2one('payment.acquirer')
    sequence = fields.Integer()
    logo = fields.Image()
    name = fields.Char(required=True)
    iban_number = fields.Char(string='IBAN')
    account_number = fields.Char()
    branch = fields.Char()
    color = fields.Char()

class PaymentAcquirerJetcheckoutJournal(models.Model):
    _name = 'payment.acquirer.jetcheckout.journal'
    _description = 'Jetcheckout Journal Items'

    acquirer_id = fields.Many2one('payment.acquirer')
    provider_id = fields.Many2one('payment.acquirer.jetcheckout.provider', required=True)
    pos_id = fields.Many2one('payment.acquirer.jetcheckout.pos', required=True)
    journal_id = fields.Many2one('account.journal', required=True)
    partner_id = fields.Many2one('res.partner', required=True, domain=[('is_company','=',True)])
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company')
    website_id = fields.Many2one('website')

class PaymentAcquirerJetcheckout(models.Model):
    _inherit = 'payment.acquirer'

    def _get_jetcheckout_url(self):
        for acq in self:
            acq.jetcheckout_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', self.env.company.name)

    @api.onchange('display_icon')
    def _compute_display_icon(self):
        for acq in self:
            if acq.display_icon:
                acq.display_icon_preview = '<i class="fa ' + acq.display_icon + '"></i>'
            else:
                acq.display_icon_preview = ''

    @api.depends('provider')
    def _compute_view_configuration_fields(self):
        """ Override of payment to hide the credentials page.
        :return: None
        """
        super()._compute_view_configuration_fields()
        self.filtered(lambda acq: acq.provider == 'transfer').write({
            'show_pre_msg': True,
        })

    provider = fields.Selection(selection_add=[('jetcheckout', 'jetcheckout')], ondelete={'jetcheckout': 'set default'})
    display_icon = fields.Char(groups='base.group_user')
    bank_ids = fields.One2many('payment.acquirer.jetcheckout.bank', 'acquirer_id', groups='base.group_user')
    display_icon_preview = fields.Html(compute='_compute_display_icon', groups='base.group_user', sanitize=False)
    jetcheckout_gateway = fields.Char(groups='base.group_user')
    jetcheckout_api_key = fields.Char(required_if_provider='jetcheckout', groups='base.group_user')
    jetcheckout_secret_key = fields.Char(required_if_provider='jetcheckout', groups='base.group_user')
    jetcheckout_url = fields.Char(compute='_get_jetcheckout_url')
    jetcheckout_journal_ids = fields.One2many('payment.acquirer.jetcheckout.journal', 'acquirer_id', groups='base.group_user')
    jetcheckout_terms = fields.Html(required_if_provider='jetcheckout', groups='base.group_user', sanitize=False, sanitize_attributes=False, sanitize_form=False)

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'jetcheckout':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_jetcheckout.payment_method_jetcheckout').id

    def _get_jetcheckout_api_url(self):
        self.ensure_one()
        return self.jetcheckout_gateway or 'https://api.jetcheckout.com'

    def _get_jetcheckout_env(self):
        return 'P' if self.state == 'enabled' else 'T'

    def _render_jetcheckout_terms(self, company, partner):
        referrer = request.httprequest.referrer
        url = referrer.split('/')
        terms = self.env['payment.acquirer.jetcheckout.term'].create({
            'company_id': company,
            'partner_id': partner,
            'domain': '//'.join([url[0],url[2]]),
        })
        return self.env['mail.render.mixin']._render_template(self.jetcheckout_terms, 'payment.acquirer.jetcheckout.term', terms.ids)[terms.id]

    @api.model
    def jetcheckout_s2s_form_process(self, kwargs):
        partner_id = int(kwargs['partner_id'])
        domain = [
            ('jetcheckout_card_holder','=',kwargs.get('cc_holder_name')),
            ('jetcheckout_card_number','=',kwargs.get('cc_number').replace(' ', '')),
            ('jetcheckout_card_expiry_month','=',kwargs.get('cc_expiry')[:2]),
            ('jetcheckout_card_expiry_year','=',kwargs.get('cc_expiry')[-2:]),
            ('jetcheckout_card_cvc','=',kwargs.get('cvc')),
            ('partner_id','=',partner_id)
        ]
        token = self.env['payment.token'].sudo().search(domain, limit=1)

        if token:
            token.jetcheckout_card_3d = kwargs.get('secure', True)
            token.jetcheckout_card_save = kwargs.get('save', False)
            token.jetcheckout_card_installment = kwargs.get('installment_id', '1')
            return token

        token = self.env['payment.token'].sudo().create({
            'acquirer_id': int(kwargs['acquirer_id']),
            'acquirer_ref': kwargs.get('cc_holder_name'),
            'jetcheckout_card_holder': kwargs.get('cc_holder_name'),
            'jetcheckout_card_number': kwargs.get('cc_number').replace(' ', ''),
            'jetcheckout_card_expiry_month': kwargs.get('cc_expiry')[:2],
            'jetcheckout_card_expiry_year': kwargs.get('cc_expiry')[-2:],
            'jetcheckout_card_cvc': kwargs.get('cvc'),
            'jetcheckout_card_3d': kwargs.get('secure', True),
            'jetcheckout_card_save': kwargs.get('save', False),
            'jetcheckout_card_installment': kwargs.get('installment_id', '1'),
            'partner_id': partner_id,
            'name': 'XXXX-XXXX-XXXX-%s - %s' % (kwargs['cc_number'][-4:], kwargs['cc_holder_name'])
        })
        #if kwargs.get('save'):
        #    card = self.iyzico_store_card(token, kwargs)
        #    if card['status'] == 'success':
        #        token.write({
        #            'iyzico_card_userkey': card['cardUserKey'],
        #            'iyzico_card_token': card['cardToken'],
        #        })
        #        return token
        return token

    def jetcheckout_s2s_form_validate(self, data):
        self.ensure_one()
        for field_name in ['cc_number', 'cvc', 'cc_holder_name', 'cc_expiry', 'installment_id']:
            if not data.get(field_name):
                return False
        return True
