# -*- coding: utf-8 -*-
import logging
import datetime
import traceback
from uuid import uuid4
from collections import Counter
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import format_date

_logger = logging.getLogger(__name__)


class PaymentSubscription(models.Model):
    _name = 'payment.subscription'
    _description = 'Payment System Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'rating.mixin']
    _check_company_auto = True
    _mail_post_access = 'read'

    @api.model
    def _default_stage(self):
        return self.env['payment.subscription.stage'].search([], order='sequence', limit=1)

    @api.model
    def _default_pricelist(self):
        return self.env['product.pricelist'].search([('currency_id', '=', self.env.company.currency_id.id)], limit=1).id

    @api.model
    def _default_template(self):
        return self.env['payment.subscription.template'].search([], limit=1)

    @api.model
    def _default_team(self):
        return self.env['crm.team']._get_default_team_id()

    @api.model
    def _default_starred_user(self):
        return [(6, 0, [self.env.uid])]

    @api.depends('line_ids', 'recurring_total')
    def _compute_amount_all(self):
        for sub in self:
            val = val1 = 0.0
            cur = sub.pricelist_id.sudo().currency_id
            for line in sub.line_ids:
                val1 += line.price_subtotal
                val += line._amount_line_tax()
            sub.recurring_amount_tax = cur.round(val)
            sub.recurring_amount_total = sub.recurring_amount_tax + sub.recurring_total

    @api.depends('line_ids', 'line_ids.quantity', 'line_ids.price_subtotal')
    def _compute_recurring_total(self):
        for sub in self:
            sub.recurring_total = sum(line.price_subtotal for line in sub.line_ids)

    @api.depends('recurring_total', 'template_id.recurring_interval', 'template_id.recurring_rule_type')
    def _compute_recurring_monthly(self):
        interval_factor = {
            'daily': 30.0,
            'weekly': 30.0 / 7.0,
            'monthly': 1.0,
            'yearly': 1.0 / 12.0,
        }
        for sub in self:
            sub.recurring_monthly = sub.recurring_total * interval_factor[sub.recurring_rule_type] / sub.recurring_interval if sub.template_id else 0

    def _compute_sale_order_count(self):
        sol = self.env['sale.order.line']
        if sol.check_access_rights('read', raise_exception=False):
            raw_data = sol.read_group(
                [('payment_subscription_id', 'in', self.ids)],
                ['payment_subscription_id', 'order_id'],
                ['payment_subscription_id', 'order_id'],
                lazy=False,
            )
            count = Counter(g['payment_subscription_id'][0] for g in raw_data)
        else:
            count = Counter()

        for sub in self:
            sub.sale_order_count = count[sub.id]

    @api.depends('uuid')
    def _compute_website_url(self):
        for sub in self:
            sub.website_url = '/my/subscriptions/%s/%s' % (sub.id, sub.uuid)

    @api.depends('rating_ids.rating')
    def _compute_percentage_satisfaction(self):
        for sub in self:
            activities = sub.rating_get_grades()
            total_activity_values = sum(activities.values())
            sub.percentage_satisfaction = activities['great'] * 100 / total_activity_values if total_activity_values else -1

    def _compute_invoice_count(self):
        Invoice = self.env['account.move']
        can_read = Invoice.check_access_rights('read', raise_exception=False)
        for sub in self:
            sub.invoice_count = can_read and Invoice.search_count([('invoice_line_ids.payment_subscription_id', '=', sub.id)]) or 0

    def _compute_starred(self):
        for sub in self:
            sub.starred = self.env.user in sub.starred_user_ids

    def _inverse_starred(self):
        starred_subscriptions = not_star_subscriptions = self.env['payment.subscription'].sudo()
        for sub in self:
            if self.env.user in sub.starred_user_ids:
                starred_subscriptions |= sub
            else:
                not_star_subscriptions |= sub
        not_star_subscriptions.write({'starred_user_ids': [(4, self.env.uid)]})
        starred_subscriptions.write({'starred_user_ids': [(3, self.env.uid)]})

    name = fields.Char(required=True, tracking=True, default=lambda self: _('New'))
    code = fields.Char(string='Reference', required=True, tracking=True, index=True, copy=False)
    description = fields.Text()
    uuid = fields.Char('UUID', default=lambda self: str(uuid4()), copy=False, required=True)
    date_start = fields.Date(string='Start Date', default=fields.Date.today)
    date_end = fields.Date(string='End Date', tracking=True, help='If set in advance, the subscription will be set to renew 1 month before the date and will be closed on the date set in this field.')
    line_ids = fields.One2many('payment.subscription.line', 'subscription_id', string='Subscription Lines', copy=True)

    stage_id = fields.Many2one('payment.subscription.stage', string='Stage', index=True, default=_default_stage, copy=False, group_expand='_read_group_stage_ids', tracking=True)
    stage_in_progress = fields.Boolean(related='stage_id.in_progress', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda s: s.env.company, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, auto_join=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    tag_ids = fields.Many2many('account.analytic.tag', string='Tags', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    pricelist_id = fields.Many2one('product.pricelist', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", string='Pricelist', default=_default_pricelist, required=True, check_company=True)
    currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id', string='Currency', readonly=True)
    reason_id = fields.Many2one('payment.subscription.reason', string='Close Reason', copy=False, tracking=True)
    template_id = fields.Many2one('payment.subscription.template', string='Subscription Template', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", required=True, default=_default_template, tracking=True, check_company=True)
    user_id = fields.Many2one('res.users', string='Salesperson', tracking=True, default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True, default=_default_team, check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    payment_token_id = fields.Many2one('payment.token', 'Payment Token', check_company=True, help='If not set, the automatic payment will fail.', domain="[('partner_id', '=', partner_id), ('company_id', '=', company_id)]")
    team_user_id = fields.Many2one('res.users', string='Team Leader', related='team_id.user_id', readonly=False)
    country_id = fields.Many2one('res.country', related='partner_id.country_id', store=True, readonly=False, compute_sudo=True)
    industry_id = fields.Many2one('res.partner.industry', related='partner_id.industry_id', store=True, readonly=False)
    invoice_currency_id = fields.Many2one('res.currency', string='Invoice Currency', required=True, readonly=False, store=True, default=lambda self: self.env.company.currency_id)

    recurring_rule_type = fields.Selection(string='Recurrence', help='Invoice automatically repeat at specified interval', related='template_id.recurring_rule_type', readonly=True)
    recurring_interval = fields.Integer(string='Repeat Every', help='Repeat every (Days/Week/Month/Year)', related='template_id.recurring_interval', readonly=True)
    recurring_next_date = fields.Date(string='Date of Next Invoice', default=fields.Date.today, help='The next invoice will be created on this date then the period will be extended.')
    recurring_invoice_day = fields.Integer('Recurring Invoice Day', copy=False, default=lambda self: fields.Date.today().day)
    recurring_total = fields.Float(string='Recurring Price', compute='_compute_recurring_total', store=True, tracking=True)
    recurring_monthly = fields.Float(string='Monthly Recurring Revenue', compute='_compute_recurring_monthly', store=True)
    recurring_amount_tax = fields.Float('Taxes', compute='_compute_amount_all')
    recurring_amount_total = fields.Float('Total', compute='_compute_amount_all')
    recurring_rule_boundary = fields.Selection(related='template_id.recurring_rule_boundary', readonly=False)

    in_progress = fields.Boolean(related='stage_id.in_progress')
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')
    to_renew = fields.Boolean(string='To Renew', default=False, copy=False)
    payment_mode = fields.Selection(related='template_id.payment_mode', readonly=False)
    website_url = fields.Char('Website URL', compute='_compute_website_url', help='The full URL to access the document through the website.')

    starred_user_ids = fields.Many2many('res.users', 'payment_subscription_starred_user_rel', 'payment_subscription_id', 'user_id', default=_default_starred_user, string='Members')
    starred = fields.Boolean(compute='_compute_starred', inverse='_inverse_starred', string='Show Subscriptions on dashboard', help='Whether this subscription should be displayed on the dashboard or not')

    kpi_1month_mrr_delta = fields.Float('KPI 1 Month MRR Delta')
    kpi_1month_mrr_percentage = fields.Float('KPI 1 Month MRR Percentage')
    kpi_3months_mrr_delta = fields.Float('KPI 3 months MRR Delta')
    kpi_3months_mrr_percentage = fields.Float('KPI 3 Months MRR Percentage')
    percentage_satisfaction = fields.Integer(string='% Happy', compute='_compute_percentage_satisfaction', store=True, default=-1, help="Calculate the ratio between the number of the best ('great') ratings and the total number of ratings")

    _sql_constraints = [
        ('uuid_uniq', 'unique (uuid)', 'UUIDs (Universally Unique IDentifier) should be unique for subscriptions!'),
    ]

    def _init_column(self, column_name):
        if column_name == 'uuid':
            _logger.debug("Table '%s': setting default value of new column %s to unique values for each row", self._table, column_name)
            self.env.cr.execute('SELECT id FROM %s WHERE uuid IS NULL' % self._table)
            acc_ids = self.env.cr.dictfetchall()
            query_list = [{'id': acc_id['id'], 'uuid': str(uuid4())} for acc_id in acc_ids]
            query = f'UPDATE {self._table} SET uuid = %(uuid)s WHERE id = %(id)s;'
            self.env.cr._obj.executemany(query, query_list)
        else:
            super(PaymentSubscription, self)._init_column(column_name)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.sudo().search([], order=order)

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'stage_id' in init_values:
            return self.env.ref('payment_system_subscription.subtype_stage_change')
        return super(PaymentSubscription, self)._track_subtype(init_values)

    def partial_order_line(self, sale_order, option_line, refund=False, date_from=False):
        lines = self.env['sale.order.line']
        ratio, message, period_msg = self._partial_recurring_invoice_ratio(date_from=date_from)
        if message != '':
            sale_order.message_post(body=message)

        discount = (1 - ratio) * 100
        values = {
            'order_id': sale_order.id,
            'product_id': option_line.product_id.id,
            'payment_subscription_id': self.id,
            'product_uom_qty': option_line.quantity,
            'product_uom': option_line.uom_id.id,
            'discount': discount,
            'price_unit': self.pricelist_id.with_context(uom=option_line.uom_id.id).get_product_price(option_line.product_id, 1, False),
            'name': option_line.name + '\n' + period_msg,
        }
        return lines.create(values)

    def _partial_recurring_invoice_ratio(self, date_from=False):
        if date_from:
            date = fields.Date.from_string(date_from)
        else:
            date = datetime.date.today()

        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        invoicing_period = relativedelta(**{periods[self.recurring_rule_type]: self.recurring_interval})
        recurring_next_invoice = fields.Date.from_string(self.recurring_next_date)
        recurring_last_invoice = recurring_next_invoice - invoicing_period
        time_to_invoice = recurring_next_invoice - date
        ratio = float(time_to_invoice.days) / float((recurring_next_invoice - recurring_last_invoice).days)
        period_msg = _('Invoicing period') + ': %s - %s' % (format_date(self.env, date), format_date(self.env, recurring_next_invoice))

        if (ratio < 0 or ratio > 1):
            message = _(
                'Discount computation failed because the upsell date is not between the next ' +
                'invoice date and the computed last invoice date. Defaulting to NO Discount policy.'
            )
            message += '<br/>{}{}<br/>{}{}<br/>{}{}'.format(
                _('Upsell date: '), format_date(self.env, date),
                _('Next invoice date: '), format_date(self.env, recurring_next_invoice),
                _('Last invoice date: '), format_date(self.env, recurring_last_invoice),
            )
            ratio = 1.00
        else:
            message = ''

        return ratio, message, period_msg

    def partial_recurring_invoice_ratio(self, date_from=False):
        return self._partial_recurring_invoice_ratio(date_from=False)[0]

    @api.model
    def default_get(self, fields):
        defaults = super(PaymentSubscription, self).default_get(fields)
        if 'code' in fields:
            defaults.update(code=self.env['ir.sequence'].next_by_code('payment.subscription') or _('New'))
        return defaults

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.pricelist_id = self.partner_id.with_company(self.company_id).property_product_pricelist.id
        if self.partner_id.user_id:
            self.user_id = self.partner_id.user_id

    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.user_id and self.user_id.sale_team_id:
            self.team_id = self.user_id.sale_team_id

    @api.onchange('date_start', 'template_id')
    def onchange_date_start(self):
        if self.date_start and self.recurring_rule_boundary == 'limited':
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            self.date = fields.Date.from_string(self.date_start) + relativedelta(**{
                periods[
                    self.recurring_rule_type]: self.template_id.recurring_rule_count * self.template_id.recurring_interval})
        else:
            self.date = False

    @api.onchange('template_id')
    def onchange_template(self):
        for sub in self.filtered('template_id'):
            sub.description = sub.template_id.description

    @api.model
    def create(self, vals):
        vals['code'] = (
                vals.get('code') or
                self.env.context.get('default_code') or
                self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code('payment.subscription') or
                _('New')
        )
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = vals['code']

        if not vals.get('recurring_invoice_day'):
            sub_date = vals.get('recurring_next_date') or vals.get('date_start') or fields.Date.context_today(self)
            if isinstance(sub_date, datetime.date):
                vals['recurring_invoice_day'] = sub_date.day
            else:
                vals['recurring_invoice_day'] = fields.Date.from_string(sub_date).day

        sub = super(PaymentSubscription, self).create(vals)
        if vals.get('stage_id'):
            sub._send_subscription_rating_mail(force_send=True)
        if sub.partner_id:
            sub.message_subscribe(sub.partner_id.ids)
        return sub

    def write(self, vals):
        recurring_next_date = vals.get('recurring_next_date')
        if recurring_next_date and not self.env.context.get('skip_update_recurring_invoice_day'):
            if isinstance(recurring_next_date, datetime.date):
                vals['recurring_invoice_day'] = recurring_next_date.day
            else:
                vals['recurring_invoice_day'] = fields.Date.from_string(recurring_next_date).day

        if vals.get('partner_id'):
            self.message_subscribe([vals['partner_id']])

        result = super(PaymentSubscription, self).write(vals)
        if vals.get('stage_id'):
            self._send_subscription_rating_mail(force_send=True)
        return result

    def unlink(self):
        self.wipe()
        self.env['payment.subscription.snapshot'].sudo().search([('subscription_id', 'in', self.ids)]).unlink()
        return super(PaymentSubscription, self).unlink()

    def name_get(self):
        res = []
        for sub in self.filtered('id'):
            partner_name = sub.partner_id.sudo().display_name
            subscription_name = '%s - %s' % (sub.code, partner_name) if sub.code else partner_name
            template_name = sub.template_id.sudo().code
            display_name = '%s/%s' % (template_name, subscription_name) if template_name else subscription_name
            res.append((sub.id, display_name))
        return res

    def action_sales(self):
        self.ensure_one()
        sales = self.env['sale.order'].search([('order_line.payment_subscription_id', 'in', self.ids)])
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'views': [
                [self.env.ref('payment_system_subscription.tree_sale').id, 'tree'],
                [self.env.ref('sale.view_order_form').id, 'form'],
                [False, 'kanban'],
                [False, 'calendar'],
                [False, 'pivot'],
                [False, 'graph']
            ],
            'domain': [['id', 'in', sales.ids]],
            'context': {'create': False},
            'name': _('Sales Orders'),
        }

    def action_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([('invoice_line_ids.payment_subscription_id', 'in', self.ids)])
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['context'] = {'create': False, 'default_type': 'out_invoice'}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.model
    def cron_account_analytic_account(self):
        today = fields.Date.today()
        next_month = fields.Date.to_string(fields.Date.from_string(today) + relativedelta(months=1))

        # set to pending if date is in less than a month
        domain_pending = [('date', '<', next_month), ('in_progress', '=', True)]
        subs_pending = self.search(domain_pending)
        subs_pending.set_to_renew()

        # set to close if date is passed
        domain_close = [('date', '<', today), '|', ('in_progress', '=', True), ('to_renew', '=', True)]
        subs_close = self.search(domain_close)
        subs_close.set_close()

        return dict(pending=subs_pending.ids, closed=subs_close.ids)

    @api.model
    def _cron_recurring_create_invoice(self):
        return self._recurring_create_invoice(automatic=True)

    @api.model
    def _cron_update_kpi(self):
        subs = self.search([('in_progress', '=', True)])
        subs._take_snapshot(datetime.date.today())
        subs._compute_kpi()

    def _take_snapshot(self, date):
        for sub in self:
            self.env['payment.subscription.snapshot'].create({
                'subscription_id': sub.id,
                'date': fields.Date.to_string(date),
                'recurring_monthly': sub.recurring_monthly,
            })

    def _get_subscription_delta(self, date):
        self.ensure_one()
        delta, percentage = False, False
        snapshot = self.env['payment.subscription.snapshot'].search([
            ('subscription_id', '=', self.id),
            ('date', '<=', date)], order='date desc', limit=1)
        if snapshot:
            delta = self.recurring_monthly - snapshot.recurring_monthly
            percentage = delta / snapshot.recurring_monthly if snapshot.recurring_monthly != 0 else 100
        return {'delta': delta, 'percentage': percentage}

    def _compute_kpi(self):
        for sub in self:
            delta_1month = sub._get_subscription_delta(datetime.date.today() - relativedelta(months=1))
            delta_3months = sub._get_subscription_delta(datetime.date.today() - relativedelta(months=3))
            sub.write({
                'kpi_1month_mrr_delta': delta_1month['delta'],
                'kpi_1month_mrr_percentage': delta_1month['percentage'],
                'kpi_3months_mrr_delta': delta_3months['delta'],
                'kpi_3months_mrr_percentage': delta_3months['percentage'],
            })

    def _send_subscription_rating_mail(self, force_send=False):
        for sub in self.filtered(lambda sub: sub.stage_id.rating_template_id):
            sub.rating_send_request(
                sub.stage_id.rating_template_id,
                lang=sub.partner_id.lang,
                force_send=force_send,
            )

    def set_to_renew(self):
        return self.write({'to_renew': True})

    def unset_to_renew(self):
        return self.write({'to_renew': False})

    def clear_date(self):
        return self.write({'date': False})

    def set_close(self):
        today = fields.Date.from_string(fields.Date.today())
        search = self.env['payment.subscription.stage'].search
        for sub in self:
            stage = search([('in_progress', '=', False), ('sequence', '>=', sub.stage_id.sequence)], limit=1)
            if not stage:
                stage = search([('in_progress', '=', False)], limit=1)
            sub.write({'stage_id': stage.id, 'to_renew': False, 'date': today})
        return True

    def set_open(self):
        search = self.env['payment.subscription.stage'].search
        for sub in self:
            stage = search([('in_progress', '=', True), ('sequence', '>=', sub.stage_id.sequence)], limit=1)
            if not stage:
                stage = search([('in_progress', '=', True)], limit=1)
            date = sub.date if sub.date_start and sub.template_id.recurring_rule_boundary == 'limited' else False
            sub.write({'stage_id': stage.id, 'to_renew': False, 'date': date})

    def _prepare_invoice_data(self):
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_('You must first select a customer for subscription %s!') % self.name)
        if 'force_company' in self.env.context:
            company = self.env['res.company'].browse(self.env.context['force_company'])
        else:
            company = self.company_id
            self = self.with_company(company)

        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
        journal = self.template_id.journal_id or self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        if not journal:
            raise UserError(_('Please define a sale journal for the company "%s".') % (company.name or '',))

        next_date = self.recurring_next_date
        if not next_date:
            raise UserError(_('Please define Date of Next Invoice of "%s".') % (self.display_name,))

        recurring_next_date = self._get_recurring_next_date(self.recurring_rule_type, self.recurring_interval, next_date, self.recurring_invoice_day)
        end_date = fields.Date.from_string(recurring_next_date) - relativedelta(days=1)
        addr = self.partner_id.address_get(['delivery', 'invoice'])

        sale_order = self.env['sale.order'].search([('order_line.payment_subscription_id', 'in', self.ids)], order='id desc', limit=1)
        use_sale_order = sale_order and sale_order.partner_id == self.partner_id
        partner_id = sale_order.partner_invoice_id.id if use_sale_order else addr['invoice']
        partner_shipping_id = sale_order.partner_shipping_id.id if use_sale_order else addr['delivery']
        narration = _('This invoice covers the following period: %s - %s') % (format_date(self.env, next_date), format_date(self.env, end_date))
        if self.description:
            narration += '\n' + self.description
        elif self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.company_id.invoice_terms:
            narration += '\n' + self.company_id.invoice_terms
        res = {
            'type': 'out_invoice',
            'partner_id': partner_id,
            'partner_shipping_id': partner_shipping_id,
            'currency_id': self.invoice_currency_id.id,
            #'currency_id': self.pricelist_id.currency_id.id,
            'journal_id': journal.id,
            'narration': narration,
            'invoice_origin': self.code,
            'fiscal_position_id': fpos_id,
            'invoice_user_id': self.user_id.id,
            'invoice_payment_term_id': sale_order.payment_term_id.id if sale_order else self.partner_id.property_payment_term_id.id,
            'invoice_partner_bank_id': company.partner_id.bank_ids.filtered(lambda b: not b.company_id or b.company_id == company)[:1].id,
        }
        if self.team_id:
            res['team_id'] = self.team_id.id
        return res

    @api.model
    def _get_recurring_next_date(self, interval_type, interval, current_date, recurring_invoice_day):
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        interval_type = periods[interval_type]
        recurring_next_date = fields.Date.from_string(current_date) + relativedelta(**{interval_type: interval})
        if interval_type == 'months':
            last_day_of_month = recurring_next_date + relativedelta(day=31)
            if last_day_of_month.day >= recurring_invoice_day:
                return recurring_next_date.replace(day=recurring_invoice_day)
            return last_day_of_month
        return recurring_next_date

    def _prepare_invoice_line(self, line, fiscal_position, date_start=False, date_stop=False):
        if 'force_company' in self.env.context:
            company = self.env['res.company'].browse(self.env.context['force_company'])
        else:
            company = line.analytic_account_id.company_id
            line = line.with_company(company)

        fpos = self.env['account.fiscal.position'].browse(fiscal_position or None)
        tax_ids = fpos.map_tax(line.product_id.taxes_id.filtered(lambda t: t.company_id == company))
        accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)

        currency_id = self.currency_id.id
        price_unit = line.price_unit
        if self.currency_id != self.invoice_currency_id:
            price_unit = line.price_unit or 0.0
            price_unit = self.currency_id.with_context(date=self.recurring_next_date).compute(price_unit, self.invoice_currency_id, round=False)
            currency_id = self.invoice_currency_id.id

        return {
            'name': line.name,
            'payment_subscription_id': line.subscription_id.id,
            'price_unit': price_unit,
            'currency_id': currency_id,
            'discount': line.discount,
            'quantity': line.quantity,
            'product_uom_id': line.uom_id.id,
            'product_id': line.product_id.id,
            'account_id': accounts['income'],
            'tax_ids': [(6, 0, tax_ids.ids)],
            'analytic_account_id': line.subscription_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, line.subscription_id.tag_ids.ids)],
            'payment_subscription_start_date': date_start,
            'payment_subscription_end_date': date_stop,
        }

    def _prepare_invoice_lines(self, fiscal_position):
        self.ensure_one()
        revenue_date_start = self.recurring_next_date
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        revenue_date_stop = revenue_date_start + relativedelta(**{periods[self.recurring_rule_type]: self.recurring_interval}) - relativedelta(days=1)
        return [(0, 0, self._prepare_invoice_line(line, fiscal_position, revenue_date_start, revenue_date_stop)) for line in self.line_ids]

    def _prepare_invoice(self):
        invoice = self._prepare_invoice_data()
        invoice['invoice_line_ids'] = self._prepare_invoice_lines(invoice['fiscal_position_id'])
        return invoice

    def recurring_invoice(self):
        self._recurring_create_invoice()
        return self.action_subscription_invoice()

    def _prepare_renewal_order_values(self):
        res = dict()
        for subscription in self:
            order_lines = []
            fpos_id = self.env['account.fiscal.position'].company_id(subscription.company_id.id).get_fiscal_position(subscription.partner_id.id)
            for line in subscription.line_ids:
                partner_lang = subscription.partner_id.lang
                product = line.product_id.with_context(lang=partner_lang) if partner_lang else line.product_id

                order_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': product.get_product_multiline_description_sale(),
                    'payment_subscription_id': subscription.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                }))
            addr = subscription.partner_id.address_get(['delivery', 'invoice'])
            sale_order = subscription.env['sale.order'].search([('order_line.payment_subscription_id', '=', subscription.id)], order='id desc', limit=1)
            res[subscription.id] = {
                'pricelist_id': subscription.pricelist_id.id,
                'partner_id': subscription.partner_id.id,
                'partner_invoice_id': addr['invoice'],
                'partner_shipping_id': addr['delivery'],
                'currency_id': subscription.pricelist_id.currency_id.id,
                'order_line': order_lines,
                'analytic_account_id': subscription.analytic_account_id.id,
                'payment_subscription_management': 'renew',
                'origin': subscription.code,
                'note': subscription.description,
                'fiscal_position_id': fpos_id,
                'user_id': subscription.user_id.id,
                'payment_term_id': sale_order.payment_term_id.id if sale_order else subscription.partner_id.property_payment_term_id.id,
                'company_id': subscription.company_id.id,
            }
        return res

    def prepare_renewal_order(self):
        self.ensure_one()
        values = self._prepare_renewal_order_values()
        order = self.env['sale.order'].create(values[self.id])
        order.message_post(body=(
            _('This renewal order has been created from the payment subscription ') + ' <a href=# data-oe-model=payment.subscription data-oe-id=%d>%s</a>' % (self.id, self.display_name)
        ))
        order.order_line._compute_tax_id()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'views': [[False, 'form']],
            'res_id': order.id,
        }

    def increment_period(self):
        for sub in self:
            current_date = sub.recurring_next_date or self.default_get(['recurring_next_date'])['recurring_next_date']
            new_date = sub._get_recurring_next_date(
                sub.recurring_rule_type,
                sub.recurring_interval, current_date,
                sub.recurring_invoice_day
            )
            sub.write({'recurring_next_date': new_date})

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|', ('code', operator, name), ('name', operator, name), ('partner_id.name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    def wipe(self):
        lines = self.mapped('line_ids')
        lines.unlink()
        return True

    def open_website_url(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.website_url,
            'target': 'self',
        }

    def add_option(self, option_id):
        pass

    def set_option(self, subscription, new_option, price):
        pass

    def remove_option(self, option_id):
        pass

    def _compute_options(self):
        pass

    def _do_payment(self, payment_token, invoice, two_steps_sec=True):
        tx_obj = self.env['payment.transaction']
        results = []

        off_session = self.env.context.get('off_session', True)
        for rec in self:
            reference = 'SUB%s-%s' % (rec.id, datetime.datetime.now().strftime('%y%m%d_%H%M%S'))
            values = {
                'amount': invoice.amount_total,
                'acquirer_id': payment_token.acquirer_id.id,
                'type': 'server2server',
                'currency_id': invoice.currency_id.id,
                'reference': reference,
                'payment_token_id': payment_token.id,
                'partner_id': rec.partner_id.id,
                'partner_country_id': rec.partner_id.country_id.id,
                'invoice_ids': [(6, 0, [invoice.id])],
                'callback_model_id': self.env['ir.model'].sudo().search([('model', '=', rec._name)], limit=1).id,
                'callback_res_id': rec.id,
                'callback_method': 'reconcile_pending_transaction' if off_session else '_reconcile_and_send_mail',
                'return_url': '/my/subscriptions/%s/%s' % (self.id, self.uuid),
            }
            tx = tx_obj.create(values)

            baseurl = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            payment_secure = {
                '3d_secure': two_steps_sec,
                'accept_url': baseurl + '/my/subscriptions/%s/payment/%s/accept/' % (rec.uuid, tx.id),
                'decline_url': baseurl + '/my/subscriptions/%s/payment/%s/decline/' % (rec.uuid, tx.id),
                'exception_url': baseurl + '/my/subscriptions/%s/payment/%s/exception/' % (rec.uuid, tx.id),
            }
            tx.with_context(off_session=off_session).s2s_do_transaction(**payment_secure)
            results.append(tx)
        return results

    def reconcile_pending_transaction(self, tx, invoice=False):
        self.ensure_one()
        if not invoice:
            invoice = tx.invoice_ids and tx.invoice_ids[0]
        if tx.state in ['done', 'authorized']:
            invoice.write({'ref': tx.reference, 'invoice_payment_ref': tx.reference})
            self.increment_period()
            self.set_open()
        else:
            invoice.button_cancel()
            invoice.unlink()

    def _reconcile_and_send_mail(self, tx, invoice=False):
        if not invoice:
            invoice = tx.invoice_ids and tx.invoice_ids[0]

        self.reconcile_pending_transaction(tx, invoice=invoice)
        self.send_success_mail(tx, invoice)
        msg_body = 'Manual payment succeeded. Payment reference: <a href=# data-oe-model=payment.transaction data-oe-id=%d>%s</a>; Amount: %s. Invoice <a href=# data-oe-model=account.move data-oe-id=%d>View Invoice</a>.' % (tx.id, tx.reference, tx.amount, invoice.id)
        self.message_post(body=msg_body)
        return True

    def _recurring_create_invoice(self, automatic=False):
        auto_commit = self.env.context.get('auto_commit', True)
        cr = self.env.cr
        invoices = self.env['account.move']
        current_date = datetime.date.today()
        imd_res = self.env['ir.model.data']
        template_res = self.env['mail.template']
        if len(self) > 0:
            subscriptions = self
        else:
            domain = [
                ('recurring_next_date', '<=', current_date),
                ('template_id.payment_mode', '!=', 'manual'),
                '|', ('in_progress', '=', True), ('to_renew', '=', True),
            ]
            subscriptions = self.search(domain)
        if subscriptions:
            sub_data = subscriptions.read(fields=['id', 'company_id'])
            for company_id in set(data['company_id'][0] for data in sub_data):
                sub_ids = [s['id'] for s in sub_data if s['company_id'][0] == company_id]
                subs = self.with_company(company_id).browse(sub_ids)
                context_invoice = dict(self.env.context, type='out_invoice')
                for subscription in subs:
                    subscription = subscription[0]
                    if automatic and auto_commit:
                        cr.commit()

                    if automatic and subscription.date and subscription.date <= current_date:
                        subscription.set_close()
                        continue

                    if subscription.template_id.payment_mode in ['validate_send_payment', 'success_payment'] and subscription.recurring_total and automatic:
                        try:
                            payment_token = subscription.payment_token_id
                            tx = None
                            if payment_token:
                                invoice_values = subscription.with_context(
                                    lang=subscription.partner_id.lang)._prepare_invoice()
                                new_invoice = self.env['account.move'].with_company(company_id).with_context(context_invoice).create(invoice_values)
                                if subscription.analytic_account_id or subscription.tag_ids:
                                    for line in new_invoice.invoice_line_ids:
                                        if subscription.analytic_account_id:
                                            line.analytic_account_id = subscription.analytic_account_id
                                        if subscription.tag_ids:
                                            line.analytic_tag_ids = subscription.tag_ids
                                new_invoice.message_post_with_view(
                                    'mail.message_origin_link',
                                    values={'self': new_invoice, 'origin': subscription},
                                    subtype_id=self.env.ref('mail.mt_note').id
                                )
                                tx = subscription._do_payment(payment_token, new_invoice, two_steps_sec=False)[0]
                                if auto_commit:
                                    cr.commit()
                                if tx.payment_renewal_allowed:
                                    msg_body = _(
                                        'Automatic payment succeeded. Payment reference: <a href=# data-oe-model=payment.transaction data-oe-id=%d>%s</a>; Amount: %s. Invoice <a href=# data-oe-model=account.move data-oe-id=%d>View Invoice</a>.') % (tx.id, tx.reference, tx.amount, new_invoice.id)
                                    subscription.message_post(body=msg_body)
                                    if subscription.template_id.payment_mode == 'validate_send_payment':
                                        subscription.validate_and_send_invoice(new_invoice)
                                    else:
                                        if new_invoice.state != 'posted':
                                            new_invoice.post()
                                    subscription.send_success_mail(tx, new_invoice)
                                    if auto_commit:
                                        cr.commit()
                                else:
                                    _logger.error('Fail to create recurring invoice for subscription %s', subscription.code)
                                    if auto_commit:
                                        cr.rollback()
                                    new_invoice.unlink()
                            if tx is None or not tx.payment_renewal_allowed:
                                amount = subscription.recurring_total
                                date_close = (
                                    subscription.recurring_next_date +
                                    relativedelta(days=subscription.template_id.auto_close_limit or 15)
                                )
                                close_subscription = current_date >= date_close
                                email_context = self.env.context.copy()
                                email_context.update({
                                    'payment_token': subscription.payment_token_id and subscription.payment_token_id.name,
                                    'renewed': False,
                                    'total_amount': amount,
                                    'email_to': subscription.partner_id.email,
                                    'code': subscription.code,
                                    'currency': subscription.pricelist_id.currency_id.name,
                                    'date_end': subscription.date,
                                    'date_close': date_close
                                })
                                if close_subscription:
                                    model, template_id = imd_res.get_object_reference('payment_subscription', 'email_payment_close')
                                    template = template_res.browse(template_id)
                                    template.with_context(email_context).send_mail(subscription.id)
                                    _logger.debug('Sending Payment Subscription Closure Mail to %s for payment subscription %s and closing payment subscription', subscription.partner_id.email, subscription.id)
                                    msg_body = _('Automatic payment failed after multiple attempts. Payment Subscription closed automatically.')
                                    subscription.message_post(body=msg_body)
                                    subscription.set_close()
                                else:
                                    model, template_id = imd_res.get_object_reference('payment_subscription', 'email_payment_reminder')
                                    msg_body = _("Automatic payment failed. Subscription set to 'To Renew'.")
                                    if (datetime.date.today() - subscription.recurring_next_date).days in [0, 3, 7, 14]:
                                        template = template_res.browse(template_id)
                                        template.with_context(email_context).send_mail(subscription.id)
                                        _logger.debug('Sending Payment Failure Mail to %s for payment subscription %s and setting payment subscription to pending', subscription.partner_id.email, subscription.id)
                                        msg_body += _(' E-mail sent to customer.')
                                    subscription.message_post(body=msg_body)
                                    subscription.set_to_renew()
                            if auto_commit:
                                cr.commit()
                        except Exception:
                            if auto_commit:
                                cr.rollback()

                            traceback_message = traceback.format_exc()
                            _logger.error(traceback_message)
                            last_tx = self.env['payment.transaction'].search([
                                ('reference', 'like', 'SUBSCRIPTION-%s-%s' % (subscription.id, datetime.date.today().strftime('%y%m%d')))
                            ], limit=1)
                            error_message = 'Error during renewal of payment subscription %s (%s)' % (
                                subscription.code,
                                'Payment recorded: %s' % last_tx.reference if last_tx and last_tx.state == 'done' else 'No payment recorded.'
                            )
                            _logger.error(error_message)

                    elif subscription.template_id.payment_mode in ['draft_invoice', 'manual', 'validate_send']:
                        try:
                            invoice_values = subscription.with_context(
                                lang=subscription.partner_id.lang)._prepare_invoice()
                            new_invoice = self.env['account.move'].with_company(company_id).with_context(
                                context_invoice).create(invoice_values)
                            if subscription.analytic_account_id or subscription.tag_ids:
                                for line in new_invoice.invoice_line_ids:
                                    if subscription.analytic_account_id:
                                        line.analytic_account_id = subscription.analytic_account_id
                                    if subscription.tag_ids:
                                        line.analytic_tag_ids = subscription.tag_ids

                            new_invoice.message_post_with_view(
                                'mail.message_origin_link',
                                values={'self': new_invoice, 'origin': subscription},
                                subtype_id=self.env.ref('mail.mt_note').id
                            )
                            invoices += new_invoice
                            next_date = subscription.recurring_next_date or current_date
                            rule, interval = subscription.recurring_rule_type, subscription.recurring_interval
                            new_date = subscription._get_recurring_next_date(rule, interval, next_date, subscription.recurring_invoice_day)
                            subscription.with_context(skip_update_recurring_invoice_day=True).write({'recurring_next_date': new_date})
                            if subscription.template_id.payment_mode == 'validate_send':
                                subscription.validate_and_send_invoice(new_invoice)
                            if automatic and auto_commit:
                                cr.commit()
                        except Exception:
                            if automatic and auto_commit:
                                cr.rollback()
                                _logger.exception('Fail to create recurring invoice for payment subscription %s', subscription.code)
                            else:
                                raise
        return invoices

    def send_success_mail(self, tx, invoice):
        imd_res = self.env['ir.model.data']
        template_res = self.env['mail.template']
        current_date = datetime.date.today()
        next_date = self.recurring_next_date or current_date
        if not self.recurring_next_date:
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            invoicing_period = relativedelta(**{periods[self.recurring_rule_type]: self.recurring_interval})
            next_date = next_date + invoicing_period
        _, template_id = imd_res.get_object_reference('payment_subscription', 'email_payment_success')
        email_context = self.env.context.copy()
        email_context.update({
            'payment_token': self.payment_token_id.name,
            'renewed': True,
            'total_amount': tx.amount,
            'next_date': next_date,
            'previous_date': self.recurring_next_date,
            'email_to': self.partner_id.email,
            'code': self.code,
            'currency': self.pricelist_id.currency_id.name,
            'date_end': self.date,
        })
        _logger.debug('Sending Payment Confirmation Mail to %s for payment subscription %s', self.partner_id.email, self.id)
        template = template_res.browse(template_id)
        return template.with_context(email_context).send_mail(invoice.id)

    def validate_and_send_invoice(self, invoice):
        self.ensure_one()
        if invoice.state != 'posted':
            invoice.post()
        email_context = self.env.context.copy()
        email_context.update({
            'total_amount': invoice.amount_total,
            'email_to': self.partner_id.email,
            'code': self.code,
            'currency': self.pricelist_id.currency_id.name,
            'date_end': self.date,
        })
        _logger.debug('Sending Invoice Mail to %s for payment subscription %s', self.partner_id.email, self.id)
        self.template_id.invoice_mail_template_id.with_context(email_context).send_mail(invoice.id)
        invoice.invoice_sent = True
        if hasattr(invoice, 'attachment_ids') and invoice.attachment_ids:
            invoice._message_set_main_attachment_id([(4, id) for id in invoice.attachment_ids.ids])

    def get_progress_subscription(self, partner_id):
        pass
