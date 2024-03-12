# -*- coding: utf-8 -*-
import re
import logging
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def _compute_payment_subscription_count(self):
        for order in self:
            order.payment_subscription_count = len(self.env['sale.order.line'].read_group(
                [('order_id', '=', order.id), ('payment_subscription_id', '!=', False)],
                ['payment_subscription_id'], ['payment_subscription_id'])
            )

    payment_subscription_count = fields.Integer(compute='_compute_payment_subscription_count')
    payment_subscription_management = fields.Selection(string='Subscription Management', selection=[
        ('create', 'Creation'),
        ('renew', 'Renewal'),
        ('upsell', 'Upselling')
        ], default='create',
        help='Creation: The Sales Order created the subscription\n'
             'Upselling: The Sales Order added lines to the subscription\n'
             'Renewal: The Sales Order replaced the subscription\'s content with its own')

    def action_subscriptions(self):
        self.ensure_one()
        subscriptions = self.order_line.mapped('payment_subscription_id')
        action = self.env.ref('payment_subscription.action_subscription').read()[0]
        if len(subscriptions) > 1:
            action['domain'] = [('id', 'in', subscriptions.ids)]
        elif len(subscriptions) == 1:
            form_view = [(self.env.ref('payment_subscription.form_subscription').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = subscriptions.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        action['context'] = dict(self._context, create=False)
        return action

    def action_draft(self):
        if any([order.state == 'cancel' and any([line.payment_subscription_id and line.payment_subscription_id.in_progress == False for line in order.order_line]) for order in self]):
            raise UserError(_('You cannot set to draft a canceled quotation linked to subscriptions. Please create a new quotation.'))
        return super(SaleOrder, self).action_draft()

    def _prepare_subscription_data(self, template):
        self.ensure_one()
        date_today = fields.Date.context_today(self)
        recurring_invoice_day = date_today.day
        recurring_next_date = self.env['payment.subscription']._get_recurring_next_date(
            template.recurring_rule_type, template.recurring_interval,
            date_today, recurring_invoice_day
        )
        values = {
            'name': template.name,
            'template_id': template.id,
            'partner_id': self.partner_invoice_id.id,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'date_start': fields.Date.context_today(self),
            'description': self.note or template.description,
            'pricelist_id': self.pricelist_id.id,
            'company_id': self.company_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'recurring_next_date': recurring_next_date,
            'recurring_invoice_day': recurring_invoice_day,
            'payment_token_id': self.transaction_ids.get_last_transaction().payment_token_id.id if template.payment_mode in ['validate_send_payment', 'success_payment'] else False
        }
        default_stage = self.env['payment.subscription.stage'].search([('in_progress', '=', True)], limit=1)
        if default_stage:
            values['stage_id'] = default_stage.id
        return values

    def update_existing_payment_subscriptions(self):
        res = []
        for order in self:
            subs = order.order_line.mapped('payment_subscription_id').sudo()
            if subs and order.payment_subscription_management != 'renew':
                order.payment_subscription_management = 'upsell'
            res.append(subs.ids)
            if order.payment_subscription_management == 'renew':
                subs.wipe()
                subs.increment_period()
                subs.set_open()
            for sub in subs:
                lines = order.order_line.filtered(lambda l: l.payment_subscription_id == sub and l.product_id.payment_recurring_invoice)
                line_ids = lines._update_payment_subscription_line_data(sub)
                sub.write({'line_ids': line_ids})
        return res

    def create_payment_subscriptions(self):
        res = []
        for order in self:
            to_create = self._split_subscription_lines()
            for template in to_create:
                values = order._prepare_payment_subscription_data(template)
                values['recurring_invoice_line_ids'] = to_create[template]._prepare_payment_subscription_line_data()
                subscription = self.env['payment.subscription'].sudo().create(values)
                subscription.onchange_date_start()
                res.append(subscription.id)
                to_create[template].write({'payment_subscription_id': subscription.id})
                subscription.message_post_with_view(
                    'mail.message_origin_link', values={'self': subscription, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id, author_id=self.env.user.partner_id.id
                )
        return res

    def _split_subscription_lines(self):
        self.ensure_one()
        res = dict()
        new_sub_lines = self.order_line.filtered(lambda l: not l.payment_subscription_id and l.product_id.payment_subscription_template_id and l.product_id.payment_recurring_invoice)
        templates = new_sub_lines.mapped('product_id').mapped('payment_subscription_template_id')
        for template in templates:
            lines = self.order_line.filtered(lambda l: l.product_id.payment_subscription_template_id == template and l.product_id.payment_recurring_invoice)
            res[template] = lines
        return res

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        self.update_existing_payment_subscriptions()
        self.create_payment_subscriptions()
        return res

    def _get_payment_type(self, tokenize=False):
        contains_subscription = any(line.product_id.payment_recurring_invoice for line in self.sudo().order_line)
        return super()._get_payment_type(tokenize=contains_subscription or tokenize)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    payment_subscription_id = fields.Many2one('sapaymentas.subscription', 'Subscription', copy=False, check_company=True)

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values) # <-- ensure_one()
        if self.payment_subscription_id:
            res.update(payment_subscription_id=self.payment_subscription_id.id)
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            next_date = self.payment_subscription_id.recurring_next_date
            previous_date = next_date - relativedelta(**{periods[self.payment_subscription_id.recurring_rule_type]: self.payment_subscription_id.recurring_interval})
            is_already_period_msg = False
            if self.order_id.payment_subscription_management != 'upsell': # renewal or creation: one entire period
                date_start = previous_date
                date_start_display = previous_date
                date_end = next_date - relativedelta(days=1) # the period does not include the next renewal date
            else:
                date_start, date_start_display, date_end = None, None, None
                try:
                    regexp = r'\[(\d{4}-\d{2}-\d{2}) -> (\d{4}-\d{2}-\d{2})\]'
                    match = re.search(regexp, self.name)
                    date_start = fields.Date.from_string(match.group(1))
                    date_start_display = date_start
                    date_end = fields.Date.from_string(match.group(2))
                except Exception:
                    _logger.error("An error occred when invoking _prepare_invoice_line: unable to compute invoicing period for %r - '%s'", self, self.name)
                if not date_start or not date_start_display or not date_end:
                    total_days = (next_date - previous_date).days
                    days = round((1 - self.discount / 100.0) * total_days)
                    date_start = next_date - relativedelta(days=days+1)
                    date_start_display = next_date - relativedelta(days=days)
                    date_end = next_date - relativedelta(days=1)
                else:
                    is_already_period_msg = True

            if not is_already_period_msg:
                lang = self.order_id.partner_invoice_id.lang
                format_date = self.env['ir.qweb.field.date'].with_context(lang=lang).value_to_html
                if lang:
                    self = self.with_context(lang=lang)

                period_msg = _('Invoicing period') + ': [%s -> %s]' % (fields.Date.to_string(date_start_display), fields.Date.to_string(date_end))
                res.update({
                    'name': res['name'] + '\n' + period_msg,
                })
            res.update({
                'payment_subscription_start_date': date_start,
                'payment_subscription_end_date': date_end,
            })
            if self.payment_subscription_id.analytic_account_id:
                res['analytic_account_id'] = self.payment_subscription_id.analytic_account_id.id
        return res

    @api.model
    def create(self, vals):
        if vals.get('order_id'):
            order = self.env['sale.order'].browse(vals['order_id'])
            Product = self.env['product.product']
            if order.origin and order.payment_subscription_management in ('upsell', 'renew') and Product.browse(vals['product_id']).payment_recurring_invoice:
                vals['payment_subscription_id'] = (
                    self.env['payment.subscription'].search(['&', ('code', '=', order.origin), ('partner_id', '=', order.partner_id.id)], limit=1).id
                    or self.env['payment.subscription'].search([('code', '=', order.origin)], limit=1).id
                )
        return super(SaleOrderLine, self).create(vals)

    def _prepare_payment_subscription_line_data(self):
        values = list()
        for line in self:
            values.append((0, False, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.product_uom_qty,
                'uom_id': line.product_uom.id,
                'price_unit': line.price_unit,
                'discount': line.discount if line.order_id.payment_subscription_management != 'upsell' else False,
            }))
        return values

    def _update_payment_subscription_line_data(self, subscription):
        values = list()
        dict_changes = dict()
        for line in self:
            sub_line = subscription.recurring_invoice_line_ids.filtered(
                lambda l: (l.product_id, l.uom_id, l.price_unit) == (line.product_id, line.product_uom, line.price_unit)
            )
            if sub_line:
                if len(sub_line) > 1:
                    sub_line[0].copy({'name': line.display_name, 'quantity': line.product_uom_qty})
                else:
                    dict_changes.setdefault(sub_line.id, sub_line.quantity)
                    dict_changes[sub_line.id] += line.product_uom_qty
            else:
                values.append(line._prepare_payment_subscription_line_data()[0])

        values += [(1, sub_id, {'quantity': dict_changes[sub_id],}) for sub_id in dict_changes]
        return values
