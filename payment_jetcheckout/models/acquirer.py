# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.http import request
from .rpc import rpc

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

    transaction_id = fields.Many2one('payment.transaction', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
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
    code = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Name must be unique')
    ]

class PaymentAcquirerJetcheckoutPos(models.Model):
    _name = 'payment.acquirer.jetcheckout.pos'
    _description = 'Jetcheckout Pos'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    provider_id = fields.Many2one('payment.acquirer.jetcheckout.provider', required=True)
    acquirer_id = fields.Many2one('payment.acquirer')

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
    journal_id = fields.Many2one('account.journal')
    partner_id = fields.Many2one('res.partner', domain=[('is_company','=',True)])
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
        """
        Override of payment to hide the credentials page.
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
    jetcheckout_api_key = fields.Char(groups='base.group_user')
    jetcheckout_secret_key = fields.Char(groups='base.group_user')
    jetcheckout_url = fields.Char(compute='_get_jetcheckout_url')
    jetcheckout_journal_ids = fields.One2many('payment.acquirer.jetcheckout.journal', 'acquirer_id', groups='base.group_user')
    jetcheckout_terms = fields.Html(required_if_provider='jetcheckout', groups='base.group_user', sanitize=False, sanitize_attributes=False, sanitize_form=False)
    jetcheckout_username = fields.Char(readonly=True)
    jetcheckout_password = fields.Char(readonly=True)
    jetcheckout_userid = fields.Integer(readonly=True)
    jetcheckout_api_name = fields.Char(readonly=True)

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
        terms = self.env['payment.acquirer.jetcheckout.term'].sudo().create({
            'company_id': company,
            'partner_id': partner,
            'domain': '//'.join([url[0],url[2]]),
        })
        return self.env['mail.render.mixin']._render_template(self.jetcheckout_terms, 'payment.acquirer.jetcheckout.term', terms.ids)[terms.id]

    def _jetcheckout_sync_providers(self):
        self.ensure_one()
        providers = self._rpc('jet.payment.org', 'search_read', [])
        items = []
        for provider in providers:
            items.append((provider['virtual_pos_infraid'][1], provider['name']))

        provider_ids = self.env['payment.acquirer.jetcheckout.provider'].sudo().search([])
        pairs = []
        for provider in provider_ids:
            if (provider.code, provider.name) not in items:
                self.env['payment.acquirer.jetcheckout.journal'].sudo().search([('provider_id','=',provider.id)]).unlink()
                self.env['payment.acquirer.jetcheckout.pos'].sudo().search([('provider_id','=',provider.id)]).unlink()
                provider.unlink()
            else:
                pairs.append((provider.code, provider.name))

        for item in items:
            if item not in pairs:
                self.env['payment.acquirer.jetcheckout.provider'].create({
                    'code': item[0],
                    'name': item[1],
                })
        return providers

    def _jetcheckout_sync_poses(self):
        self.ensure_one()
        poses = self._rpc('jet.virtual.pos', 'search_read', [('user_id', '=', self.jetcheckout_userid)])
        items = []
        for pos in poses:
            items.append((self.id, pos['payment_org_id'][1], pos['name']))

        pos_ids = self.env['payment.acquirer.jetcheckout.pos'].sudo().search([('acquirer_id','=',self.id)])
        pairs = []
        for pos in pos_ids:
            if (self.id, pos.provider_id.name, pos.name) not in items:
                self.env['payment.acquirer.jetcheckout.journal'].sudo().search([('pos_id','=',pos.id)]).unlink()
                pos.unlink()
            else:
                pairs.append((self.id, pos.provider_id.name, pos.name))

        for item in items:
            if item not in pairs:
                self.env['payment.acquirer.jetcheckout.pos'].create({
                    'acquirer_id': item[0],
                    'provider_id': self.env['payment.acquirer.jetcheckout.provider'].sudo().search([('name','=',item[1])], limit=1).id,
                    'name': item[2],
                })
        return poses

    def _rpc(self, *args):
        self.ensure_one()
        return rpc.execute(self.jetcheckout_userid, self.jetcheckout_password, *args)

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

    def action_jetcheckout_signin(self):
        self.ensure_one()
        wizard = self.env['payment.acquirer.jetcheckout.signin'].create({'acquirer_id': self.id})
        action = self.env.ref('payment_jetcheckout.action_signin').sudo().read()[0]
        action['res_id'] = wizard.id
        action['context'] = {'dialog_size': 'small'}
        return action

    def action_jetcheckout_signup(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'https://app.jetcheckout.com/web/signup'
        }

    def action_jetcheckout_signout(self):
        self.ensure_one()
        self.jetcheckout_username = False
        self.jetcheckout_password = False
        self.jetcheckout_userid = False
        self.jetcheckout_api_key = False
        self.jetcheckout_secret_key = False
        self.jetcheckout_journal_ids = [(5, 0, 0)]

    def _jetcheckout_create_poses(self, poses, apps, parent=None):
        records = self.env['payment.acquirer.jetcheckout.api.pos']
        campaigns = self.env['payment.acquirer.jetcheckout.api.campaign']
        records.search([]).unlink()
        campaigns.search([]).unlink()
        for pos in poses:
            ids = []
            for app in apps:
                if app.res_id in pos['applications']:
                    ids.append(app.id)

            records.create({
                'res_id': pos['id'],
                'acquirer_id': self.id,
                'name': pos['name'],
                'parent_id': parent.id if parent else False,
                'provider_id': self.env['payment.acquirer.jetcheckout.provider'].search([('name','=',pos['payment_org_id'][1])], limit=1).id,
                'is_active': pos['is_active'],
                'is_client_active': pos['is_client_active'],
                'is_merchant_active': pos['is_merchant_active'],
                'is_apikey_active': pos['is_apikey_active'],
                'is_terminal_active': pos['is_terminal_active'],
                'is_username_active': pos['is_username_active'],
                'is_password_active': pos['is_password_active'],
                'is_refid_active': pos['is_refid_active'],
                'is_rfnd_username_active': pos['is_rfnd_username_active'],
                'is_rfnd_password_active': pos['is_rfnd_password_active'],
                'client_id': pos['client_id'],
                'merchant_id': pos['merchant_id'],
                'terminal_id': pos['terminal_id'],
                'api_key': pos['api_key'],
                'secret_key': pos['secret_key'],
                'username': pos['username'],
                'password': pos['password'],
                'rfnd_username': pos['rfnd_username'],
                'rfnd_password': pos['rfnd_password'],
                'ref_id': pos['ref_id'],
                'priority': pos['priority'],
                'usage_3d': pos['usage_3d'],
                'mode': pos['mode'],
                'notes': pos['notes'],
                'customer_ip': pos['customer_ip'],
                'customer_email': pos['customer_email'],
                'customer_name': pos['customer_name'],
                'customer_surname': pos['customer_surname'],
                'customer_address': pos['customer_address'],
                'customer_phone': pos['customer_phone'],
                'customer_id': pos['customer_id'],
                'customer_identity': pos['customer_identity'],
                'customer_city': pos['customer_city'],
                'customer_country': pos['customer_country'],
                'customer_postal_code': pos['customer_postal_code'],
                'customer_company': pos['customer_company'],
                'basket_item_id': pos['basket_item_id'],
                'basket_item_name': pos['basket_item_name'],
                'basket_item_desc': pos['basket_item_desc'],
                'basket_item_categ': pos['basket_item_categ'],
                'billing_address_contact': pos['billing_address_contact'],
                'billing_address': pos['billing_address'],
                'billing_address_city': pos['billing_address_city'],
                'billing_address_country': pos['billing_address_country'],
                'shipping_address': pos['shipping_address'],
                'shipping_address_city': pos['shipping_address_city'],
                'shipping_address_country': pos['shipping_address_country'],
                'application_ids': [(6, 0, ids)],
                'campaign_ids': [(0, 0, {
                    'res_id': campaign['id'],
                    'offer_name': campaign['offer_name'],
                    'currency_id': campaign['currency_id'][0],
                    'is_active': campaign['is_active'],
                    'from_date': campaign['from_date'],
                    'to_date': campaign['to_date'],
                    'card_family_names': campaign['card_family_names'],
                    'installments': campaign['installments'],
                    'installment_ids': [(0, 0, {
                        'res_id': installment['id'],
                        'installment_type': installment['installment_type'],
                        'customer_rate': installment['customer_rate'],
                        'cost_rate': installment['cost_rate'],
                        'is_active': installment['is_active'],
                        'plus_installment': installment['plus_installment'],
                        'plus_installment_description': installment['plus_installment_description'],
                    }) for installment in self._rpc('jet.pos.price.line', 'search_read', [('pos_price_id', '=', campaign['id'])])],
                    'family_ids': [(0, 0, {
                        'res_id': family['id'],
                        'name': family['name'],
                    }) for family in self._rpc('jet.card.family', 'search_read', [('id', 'in', campaign['card_families'])])],
                    'excluded_bin_ids': [(0, 0, {
                        'res_id': family['id'],
                        'name': family['code'],
                    }) for family in self._rpc('jet.bin', 'search_read', [('id', 'in', campaign['excluded_bins'])])],
                }) for campaign in self._rpc('jet.pos.price', 'search_read', [('virtual_pos_id', '=', pos['id'])])],
            })

    def _jetcheckout_create_applications(self, apps, parent=None):
        records = self.env['payment.acquirer.jetcheckout.api.application']
        records.search([]).unlink()
        for app in apps:
            records |= records.create({
                'acquirer_id': self.id,
                'res_id': app['id'],
                'parent_id': parent.id if parent else False,
                'name': app['name'],
                'application_id': app['application_id'],
                'secret_key': app['secret_key'],
                'is_active': app['is_active'],
                'first_selection': app['first_selection'],
                'second_selection': app['second_selection'],
                'third_selection': app['third_selection'],
                'virtual_poses': app['virtual_poses'],
            })
        return records

    def action_jetcheckout_pos(self):
        self.ensure_one()

        vals = self._rpc('jet.application', 'search_read', [('user_id', '=', self.jetcheckout_userid)])
        parent = self.env['payment.acquirer.jetcheckout.api.poses'].create({'acquirer_id': self.id})


        self._jetcheckout_sync_providers()
        poses = self._jetcheckout_sync_poses()
        apps = self._jetcheckout_create_applications(vals)
        self._jetcheckout_create_poses(poses, apps, parent)

        action = self.env.ref('payment_jetcheckout.action_api_poses').sudo().read()[0]
        action['res_id'] = parent.id
        action['context'] = {'dialog_size': 'large'}
        return action

    def action_jetcheckout_application(self):
        self.ensure_one()

        vals = self._rpc('jet.application', 'search_read', [('user_id', '=', self.jetcheckout_userid)])
        parent = self.env['payment.acquirer.jetcheckout.api.applications'].create({'acquirer_id': self.id})

        self._jetcheckout_sync_providers()
        poses = self._jetcheckout_sync_poses()
        apps = self._jetcheckout_create_applications(vals, parent)
        self._jetcheckout_create_poses(poses, apps)

        action = self.env.ref('payment_jetcheckout.action_api_applications').sudo().read()[0]
        action['res_id'] = parent.id
        action['context'] = {'dialog_size': 'large'}
        return action
