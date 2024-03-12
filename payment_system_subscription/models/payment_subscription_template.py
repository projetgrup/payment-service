# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class PaymentSubscriptionTemplate(models.Model):
    _name = 'payment.subscription.template'
    _description = 'Payment Subscription Template'
    _inherit = 'mail.thread'
    _check_company_auto = True

    def _compute_subscription_count(self):
        subs = self.env['payment.subscription'].read_group(
            domain=[('template_id', 'in', self.ids), ('stage_id', '!=', False)],
            fields=['template_id'],
            groupby=['template_id']
        )
        data = dict([(s['template_id'][0], s['template_id_count']) for s in subs])
        for template in self:
            template.subscription_count = data.get(template.id, 0)

    def _compute_product_count(self):
        data = self.env['product.template'].sudo().read_group(
            [('payment_subscription_template_id', 'in', self.ids)],
            ['payment_subscription_template_id'],
            ['payment_subscription_template_id'],
        )
        result = dict((d['payment_subscription_template_id'][0], d['payment_subscription_template_id_count']) for d in data)
        for template in self:
            template.product_count = result.get(template.id, 0)

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    code = fields.Char()
    color = fields.Integer()
    description = fields.Text(translate=True, string='Terms and Conditions')

    recurring_rule_type = fields.Selection([
        ('daily', 'Days'),
        ('weekly', 'Weeks'),
        ('monthly', 'Months'),
        ('yearly', 'Years'),
    ], string='Recurrence', required=True, default='monthly', tracking=True, help='Invoice automatically repeat at specified interval')
    recurring_interval = fields.Integer(string='Invoicing Period', help='Repeat every (Days/Week/Month/Year)', required=True, default=1, tracking=True)
    recurring_rule_boundary = fields.Selection([
        ('unlimited', 'Forever'),
        ('limited', 'Fixed')
    ], string='Duration', default='unlimited')
    recurring_rule_count = fields.Integer(string='End After', default=1)
    recurring_rule_type_readonly = fields.Selection(string='Recurrence Unit', related='recurring_rule_type', readonly=True, tracking=False)

    product_count = fields.Integer(compute='_compute_product_count')
    subscription_count = fields.Integer(compute='_compute_subscription_count')
    user_closable = fields.Boolean(string='Closable by Customer', help='If checked, the user will be able to close his account from the frontend')
    payment_mode = fields.Selection([
        ('manual', 'Manually'),
        ('draft_invoice', 'Draft'),
        ('validate_send', 'Send'),
        ('validate_send_payment', 'Send & try to charge'),
        ('success_payment', 'Send after successful payment'),
    ], required=True, default='draft_invoice')
    auto_close_limit = fields.Integer(
        string='Automatic Closing', default=15,
        help='If the chosen payment method has failed to renew the subscription after this time, '
             'the subscription is automatically closed.'
    )

    product_ids = fields.One2many('product.template', 'payment_subscription_template_id', copy=True)
    tag_ids = fields.Many2many(
        'account.analytic.tag', 'payment_subscription_template_tag_rel',
        'template_id', 'tag_id', string='Tags',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    company_id = fields.Many2one('res.company', index=True)
    journal_id = fields.Many2one(
        'account.journal', string='Accounting Journal',
        domain="[('type', '=', 'sale')]", company_dependent=True, check_company=True,
        help='If set, subscriptions with this template will invoice in this journal; '
             'otherwise the sales journal with the lowest sequence is used.'
    )
    invoice_mail_template_id = fields.Many2one(
        'mail.template', string='Invoice Email Template', domain=[('model', '=', 'account.move')],
        default=lambda self: self.env.ref('payment_system_subscription.mail_template_payment_subscription_invoice', raise_if_not_found=False)
    )

    @api.constrains('recurring_interval')
    def _check_recurring_interval(self):
        for template in self:
            if template.recurring_interval <= 0:
                raise ValidationError(_('The recurring interval must be positive'))

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            connector = '&' if operator in expression.NEGATIVE_TERM_OPERATORS else '|'
            domain = [connector, ('code', operator, name), ('name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    def name_get(self):
        res = []
        for sub in self:
            name = '%s - %s' % (sub.code, sub.name) if sub.code else sub.name
            res.append((sub.id, name))
        return res
