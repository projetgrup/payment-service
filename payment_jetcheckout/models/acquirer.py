# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
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

    date = fields.Datetime(readonly=True)
    name = fields.Char(readonly=True)
    successful = fields.Boolean(readonly=True)
    completed = fields.Boolean(readonly=True)
    cancelled = fields.Boolean(readonly=True)
    refunded = fields.Boolean(readonly=True)
    threed = fields.Boolean(readonly=True)
    currency_id =fields.Many2one('res.currency', readonly=True)
    amount = fields.Monetary(readonly=True)
    commission_amount = fields.Monetary(readonly=True)
    commission_rate = fields.Float(readonly=True)
    customer_amount = fields.Monetary(readonly=True, string='Customer Commission Amount')
    customer_rate = fields.Float(readonly=True, string='Customer Commission Rate')
    auth_code = fields.Char(readonly=True)
    service_ref_id = fields.Char(readonly=True)


class PaymentAcquirerJetcheckoutRefund(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.refund'
    _description = 'Jetcheckout Refund'

    transaction_id = fields.Many2one('payment.transaction', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    total = fields.Monetary(readonly=True, required=True)
    amount = fields.Monetary()

    def confirm(self):
        if self.amount > self.total:
            raise UserError(_('Refund amount cannot be higher than total amount'))
        self.transaction_id._jetcheckout_api_refund(amount=self.amount)
        return {'type': 'ir.actions.act_window_close'}


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


class PaymentAcquirerJetcheckoutCampaign(models.Model):
    _name = 'payment.acquirer.jetcheckout.campaign'
    _description = 'Jetcheckout Campaign'

    acquirer_id = fields.Many2one('payment.acquirer')
    name = fields.Char(required=True)


class PaymentAcquirerJetcheckoutJournal(models.Model):
    _name = 'payment.acquirer.jetcheckout.journal'
    _description = 'Jetcheckout Journal Items'

    acquirer_id = fields.Many2one('payment.acquirer')
    name = fields.Char(required=True, readonly=True)
    journal_id = fields.Many2one('account.journal')
    partner_id = fields.Many2one('res.partner', domain=[('is_company','=',True)])
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id, readonly=True)
    company_id = fields.Many2one('res.company', ondelete='cascade')
    website_id = fields.Many2one('website', ondelete='cascade')


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
    display_icon_preview = fields.Html(compute='_compute_display_icon', groups='base.group_user', sanitize=False)
    jetcheckout_bank_ids = fields.One2many('payment.acquirer.jetcheckout.bank', 'acquirer_id', groups='base.group_user')
    jetcheckout_gateway_api = fields.Char(groups='base.group_user', readonly=True)
    jetcheckout_gateway_app = fields.Char(groups='base.group_user', readonly=True)
    jetcheckout_gateway_database = fields.Char(groups='base.group_user', readonly=True)
    jetcheckout_payment_page = fields.Boolean('Show Payment Page')
    jetcheckout_api_key = fields.Char(groups='base.group_user')
    jetcheckout_secret_key = fields.Char(groups='base.group_user')
    jetcheckout_url = fields.Char(compute='_get_jetcheckout_url')
    jetcheckout_journal_ids = fields.One2many('payment.acquirer.jetcheckout.journal', 'acquirer_id', groups='base.group_user')
    jetcheckout_campaign_ids = fields.One2many('payment.acquirer.jetcheckout.campaign', 'acquirer_id', groups='base.group_user')
    jetcheckout_terms = fields.Html(required_if_provider='jetcheckout', groups='base.group_user', sanitize=False, sanitize_attributes=False, sanitize_form=False)
    jetcheckout_no_terms = fields.Boolean('Hide Terms')
    jetcheckout_username = fields.Char(readonly=True)
    jetcheckout_password = fields.Char(readonly=True)
    jetcheckout_user_id = fields.Integer(readonly=True)
    jetcheckout_api_name = fields.Char(readonly=True)

    @api.model
    def _get_acquirer(self, company=None, website=None, providers=None, limit=None, raise_exception=True):
        self = self.sudo()
        domain = [('state', 'in', ('enabled', 'test'))]
        if providers:
            domain.append(('provider', 'in', providers))
        if self.env['res.company'].search_count([]) > 1:
            company = company or self.env.company
            domain.append(('company_id', '=', company.id))
            if website and self.env['website'].search_count([('company_id', '=', company.id)]) > 1:
                domain.append(('website_id', '=', website.id))

        acquirer = self.search(domain, limit=limit, order='sequence')
        if not acquirer:
            if raise_exception:
                raise ValidationError(_('Payment acquirer not found. Please contact with system administrator'))
        return acquirer

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'jetcheckout':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_jetcheckout.payment_method_jetcheckout').id

    def _get_jetcheckout_api_url(self):
        self.ensure_one()
        return self.jetcheckout_gateway_api or 'https://api.jetcheckout.com'

    def _get_jetcheckout_env(self):
        return 'P' if self.state == 'enabled' else 'T'

    def _render_jetcheckout_terms(self, company, partner):
        domain = self.env.context.get('domain', '')
        if domain:
            parts = domain.split('/')
            domain = '//'.join([parts[0], parts[2]])
        terms = self.env['payment.acquirer.jetcheckout.term'].sudo().create({
            'company_id': company,
            'partner_id': partner,
            'domain': domain,
        })
        return self.env['mail.render.mixin']._render_template(self.jetcheckout_terms, 'payment.acquirer.jetcheckout.term', terms.ids, engine='inline_template')[terms.id]

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

        return self.env['payment.token'].sudo().create({
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
        self.jetcheckout_user_id = False
        self.jetcheckout_api_key = False
        self.jetcheckout_secret_key = False
        self.jetcheckout_journal_ids = [(5, 0, 0)]

    def action_jetcheckout_pos(self):
        self.ensure_one()
        pos = self.env['payment.acquirer.jetcheckout.api.poses'].create({'acquirer_id': self.id, 'application_id': self.jetcheckout_api_key})
        self._jetcheckout_api_connect(pos)
        action = self.env.ref('payment_jetcheckout.action_api_poses').sudo().read()[0]
        action['res_id'] = pos.id
        action['context'] = {'dialog_size': 'large', 'create': False, 'delete': False, 'pos': True}
        return action

    def action_jetcheckout_application(self):
        self.ensure_one()
        app = self.env['payment.acquirer.jetcheckout.api.applications'].create({'acquirer_id': self.id})
        self._jetcheckout_api_connect(app)
        action = self.env.ref('payment_jetcheckout.action_api_applications').sudo().read()[0]
        action['res_id'] = app.id
        action['context'] = {'dialog_size': 'large', 'create': False, 'delete': False, 'application': True}
        return action

    def _rpc(self, *args):
        if not len(self) == 1:
            return

        url = self.jetcheckout_gateway_app or 'https://app.jetcheckout.com/jsonrpc'
        database = self.jetcheckout_gateway_database or 'jetcheckout'
        return rpc.execute(url, database, self.jetcheckout_user_id, self.jetcheckout_password, *args)

    def _jetcheckout_api_vacuum(self):
        self.env['payment.acquirer.jetcheckout.api.application'].search([]).unlink()
        self.env['payment.acquirer.jetcheckout.api.pos'].search([]).unlink()
        self.env['payment.acquirer.jetcheckout.api.campaign'].search([]).unlink()
        self.env['payment.acquirer.jetcheckout.api.installment'].search([]).unlink()
        self.env['payment.acquirer.jetcheckout.api.excluded'].search([]).unlink()
        self.env['payment.acquirer.jetcheckout.api.bank'].search([]).unlink()
        self.env['payment.acquirer.jetcheckout.api.family'].search([]).unlink()
        self.env['payment.acquirer.jetcheckout.api.provider'].search([]).unlink()
        self.env['payment.acquirer.jetcheckout.api.currency'].search([]).unlink()

    def _jetcheckout_api_create_currencies(self):
        currency_table = self.env['payment.acquirer.jetcheckout.api.currency']
        currencies = self._rpc('res.currency', 'search_read', [])
        for currency in currencies:
            currency_table.create({
                'res_id': currency['id'],
                'name': currency['name'],
            })
        return {item['res_id']: item['id'] for item in currency_table.search_read([], ['id', 'res_id'])}

    def _jetcheckout_api_create_providers(self):
        providers = self._rpc('jet.payment.org', 'search_read', [])
        pos_infra_ids = [provider['virtual_pos_infraid'][0] for provider in providers]
        pos_infras = self._rpc('jet.virtual.pos.infra', 'search_read', [('id', 'in', pos_infra_ids)])
        provider_table = self.env['payment.acquirer.jetcheckout.api.provider']
        for provider in providers:
            vals = {
                'res_id': provider['id'],
                'code': provider['virtual_pos_infraid'][1],
                'name': provider['name'],
            }

            pos_infra = list(filter(lambda x: x['id'] == provider['virtual_pos_infraid'][0], pos_infras))
            if pos_infra:
                vals.update({
                    'customer_ip': pos_infra[0]['customer_ip'],
                    'customer_email': pos_infra[0]['customer_email'],
                    'customer_name': pos_infra[0]['customer_name'],
                    'customer_surname': pos_infra[0]['customer_surname'],
                    'customer_address': pos_infra[0]['customer_address'],
                    'customer_phone': pos_infra[0]['customer_phone'],
                    'customer_id': pos_infra[0]['customer_id'],
                    'customer_identity': pos_infra[0]['customer_identity'],
                    'customer_city': pos_infra[0]['customer_city'],
                    'customer_country': pos_infra[0]['customer_country'],
                    'customer_postal_code': pos_infra[0]['customer_postal_code'],
                    'customer_company': pos_infra[0]['customer_company'],
                    'basket_item_id': pos_infra[0]['basket_item_id'],
                    'basket_item_name': pos_infra[0]['basket_item_name'],
                    'basket_item_desc': pos_infra[0]['basket_item_desc'],
                    'basket_item_categ': pos_infra[0]['basket_item_categ'],
                    'billing_address_contact': pos_infra[0]['billing_address_contact'],
                    'billing_address': pos_infra[0]['billing_address'],
                    'billing_address_city': pos_infra[0]['billing_address_city'],
                    'billing_address_country': pos_infra[0]['billing_address_country'],
                    'shipping_address': pos_infra[0]['shipping_address'],
                    'shipping_address_city': pos_infra[0]['shipping_address_city'],
                    'shipping_address_country': pos_infra[0]['shipping_address_country'],
                    'merchant_active': pos_infra[0]['merchant_active'],
                    'client_active': pos_infra[0]['client_active'],
                    'apikey_active': pos_infra[0]['apikey_active'],
                    'terminal_active': pos_infra[0]['terminal_active'],
                    'username_active': pos_infra[0]['username_active'],
                    'password_active': pos_infra[0]['password_active'],
                    'refid_active': pos_infra[0]['refId_active'],
                    'rfnd_username_active': pos_infra[0]['rfnd_username_active'],
                    'rfnd_password_active': pos_infra[0]['rfnd_password_active'],
                })

            provider_table.create(vals)
        return {item['res_id']: item['id'] for item in provider_table.search_read([], ['id', 'res_id'])}

    def _jetcheckout_api_create_application(self, record):
        application_table = self.env['payment.acquirer.jetcheckout.api.application']
        domain = [('user_id', '=', self.jetcheckout_user_id)]
        if record._name == 'payment.acquirer.jetcheckout.api.poses':
            domain.append(('application_id', '=', self.jetcheckout_api_key))
        apps = self._rpc('jet.application', 'search_read', domain)
        for app in apps:
            application_table.create({
                'acquirer_id': self.id,
                'res_id': app['id'],
                'parent_id': record.id if record._name == 'payment.acquirer.jetcheckout.api.applications' else False,
                'name': app['name'],
                'application_id': app['application_id'],
                'secret_key': app['secret_key'],
                'is_active': app['is_active'],
                'first_selection': app['first_selection'],
                'second_selection': app['second_selection'],
                'third_selection': app['third_selection'],
                'virtual_poses': app['virtual_poses'],
                'in_use': app['application_id'] == self.jetcheckout_api_key,
            })
        return {item['res_id']: item['id'] for item in application_table.search_read([], ['id', 'res_id'])}

    def _jetcheckout_api_create_pos(self, poses, apps, providers, currencies, record):
        pos_ids = [pos['id'] for pos in poses]
        pos_prices = self._rpc('jet.pos.price', 'search_read', [('virtual_pos_id', 'in', pos_ids)])
        pos_price_ids = [price['id'] for price in pos_prices]
        pos_lines = self._rpc('jet.pos.price.line', 'search_read', [('pos_price_id', 'in', pos_price_ids)])
        families = self._rpc('jet.card.family', 'search_read', [])
        bins = self._rpc('jet.bin', 'search_read', [])

        for pos in poses:
            ids = []
            for key, val in apps.items():
                if key in pos['applications']:
                    ids.append(val)

            self.env['payment.acquirer.jetcheckout.api.pos'].create({
                'res_id': pos['id'],
                'acquirer_id': self.id,
                'name': pos['name'],
                'parent_id': record.id if record._name == 'payment.acquirer.jetcheckout.api.poses' else False,
                'payment_org_id': providers[pos['payment_org_id'][0]],
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
                'applications': [(6, 0, ids)],
                'pos_price': [(0, 0, {
                    'res_id': price['id'],
                    'offer_name': price['offer_name'],
                    'currency_id': currencies[price['currency_id'][0]],
                    'is_active': price['is_active'],
                    'from_date': price['from_date'],
                    'to_date': price['to_date'],
                    'card_family_names': price['card_family_names'],
                    'installments': price['installments'],
                    'pos_lines': [(0, 0, {
                        'res_id': line['id'],
                        'installment_type': line['installment_type'],
                        'customer_rate': line['customer_rate'],
                        'cost_rate': line['cost_rate'],
                        'is_active': line['is_active'],
                        'plus_installment': line['plus_installment'],
                        'plus_installment_description': line['plus_installment_description'],
                    }) for line in pos_lines if line['pos_price_id'][0] == price['id']],
                    'card_families': [(0, 0, {
                        'res_id': family['id'],
                        'name': family['name'],
                        'logo': family['logo_path'],
                    }) for family in families if family['id'] in price['card_families']],
                    'excluded_bins': [(0, 0, {
                        'res_id': bin['id'],
                        'name': bin['code'],
                    }) for bin in bins if bin['id'] in price['excluded_bins']],
                }) for price in pos_prices if price['virtual_pos_id'][0] == pos['id']],
            })

    def _jetcheckout_api_create(self, poses, record):
        currencies = self._jetcheckout_api_create_currencies()
        providers = self._jetcheckout_api_create_providers()
        apps = self._jetcheckout_api_create_application(record)
        self._jetcheckout_api_create_pos(poses, apps, providers, currencies, record)

    def _jetcheckout_api_read(self):
        data = {}
        data['payment.acquirer.jetcheckout.api.pos'] = {item['id']: item['res_id'] for item in self.env['payment.acquirer.jetcheckout.api.pos'].search_read([], ['id', 'res_id'])}
        data['payment.acquirer.jetcheckout.api.provider'] = {item['id']: item['res_id'] for item in self.env['payment.acquirer.jetcheckout.api.provider'].search_read([], ['id', 'res_id'])}
        data['payment.acquirer.jetcheckout.api.application'] = {item['id']: item['res_id'] for item in self.env['payment.acquirer.jetcheckout.api.application'].search_read([], ['id', 'res_id'])}
        data['payment.acquirer.jetcheckout.api.campaign'] = {item['id']: item['res_id'] for item in self.env['payment.acquirer.jetcheckout.api.campaign'].search_read([], ['id', 'res_id'])}
        data['payment.acquirer.jetcheckout.api.installment'] = {item['id']: item['res_id'] for item in self.env['payment.acquirer.jetcheckout.api.installment'].search_read([], ['id', 'res_id'])}
        data['payment.acquirer.jetcheckout.api.excluded'] = {item['id']: item['res_id'] for item in self.env['payment.acquirer.jetcheckout.api.excluded'].search_read([], ['id', 'res_id'])}
        data['payment.acquirer.jetcheckout.api.family'] = {item['id']: item['res_id'] for item in self.env['payment.acquirer.jetcheckout.api.family'].search_read([], ['id', 'res_id'])}
        data['payment.acquirer.jetcheckout.api.currency'] = {item['id']: item['res_id'] for item in self.env['payment.acquirer.jetcheckout.api.currency'].search_read([], ['id', 'res_id'])}
        data['acquirer'] = self
        return data

    def _jetcheckout_api_sync_campaign(self, poses):
        api_campaigns_list = poses.filtered(lambda x: x.is_active).mapped('pos_price').filtered(lambda x: x.is_active).mapped('offer_name')
        acq_campaigns_list = self.jetcheckout_campaign_ids.mapped('name')
        api_campaigns = set(api_campaigns_list)
        acq_campaigns = set(acq_campaigns_list)
        creates = []
        unlinks = []

        for campaign in acq_campaigns:
            if campaign not in api_campaigns:
                unlinks.append(campaign)

        for campaign in api_campaigns:
            if campaign not in acq_campaigns:
                creates.append(campaign)

        self.env['payment.acquirer.jetcheckout.campaign'].sudo().search([('acquirer_id', '=', self.id), ('name', 'in', unlinks)]).unlink()
        self.env['payment.acquirer.jetcheckout.campaign'].sudo().create([{
            'acquirer_id': self.id,
            'name': name,
        } for name in creates])


    def _jetcheckout_api_upload_vals(self, vals, data, table):
        values = {}
        fields = table._fields.values()
        for field in fields:
            if field.name in vals:
                if field.type == 'one2many':
                    val_list = []
                    for val in vals[field.name]:
                        if val[0] == 0:
                            v = self._jetcheckout_api_upload_vals(val[2], data, self.env[field.comodel_name])
                            val_list.append([0, 0, v])
                        elif val[0] == 1:
                            i = data[field.comodel_name][val[1]]
                            v = self._jetcheckout_api_upload_vals(val[2], data, self.env[field.comodel_name])
                            val_list.append([1, i, v])
                        elif val[0] == 2:
                            i = data[field.comodel_name][val[1]]
                            val_list.append([2, i, 0])
                    values.update({field.name: val_list})
                elif field.type == 'many2one':
                    values.update({field.name: data[field.comodel_name][vals[field.name]]})
                elif field.type == 'many2many':
                    ids = vals[field.name][0][2]
                    values.update({field.name: [[6, 0, [data[field.comodel_name][id] for id in ids]]]})
                else:
                    values.update({field.name: vals[field.name]})
        return values

    def _jetcheckout_api_upload(self, vals, data, table):
        vals = self._jetcheckout_api_upload_vals(vals, data, table)
        fields = table._fields.values()
        for field in fields:
            if field.name in vals:
                if field.type == 'one2many':
                    name = self.env[field.comodel_name]._remote_name
                    for val in vals[field.name]:
                        if val[0] == 0:
                            self._rpc(name, 'create', val[2])
                        elif val[0] == 1:
                            self._rpc(name, 'write', val[1], val[2])
                        elif val[0] == 2:
                            self._rpc(name, 'unlink', val[1])

    def _jetcheckout_api_connect(self, record):
        # Get all data
        domain = [('user_id', '=', self.jetcheckout_user_id)]
        if record._name == 'payment.acquirer.jetcheckout.api.poses':
            domain.append(('applications.application_id', '=', self.jetcheckout_api_key))
        poses = self._rpc('jet.virtual.pos', 'search_read', domain)

        # Vacuum old data
        self._jetcheckout_api_vacuum()

        # Create transient records
        self._jetcheckout_api_create(poses, record)
