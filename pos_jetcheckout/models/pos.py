# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    jetcheckout_link_duration = fields.Integer(string='Payment Link Lifetime', default=300)
    jetcheckout_branch_code = fields.Char(string='Store Code')
    jetcheckout_physical_single_ids = fields.One2many('pos.payment.method.physical.single', 'config_id', string='Physical PoS List for Single Payments')

    @api.constrains('jetcheckout_link_duration')
    def _check_link_duration(self):
        for config in self:
            if not config.jetcheckout_link_duration > 0:
                raise ValidationError(_('Payment link lifetime cannot be lower than zero'))


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    jetcheckout_link_url = fields.Char(string='Server Address', copy=False)
    jetcheckout_link_apikey = fields.Char(string='API Key', copy=False)
    jetcheckout_link_secretkey = fields.Char(string='Secret Key', copy=False)

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [
            ('jetcheckout_virtual', 'Jetcheckout Virtual PoS'),
            ('jetcheckout_physical', 'Jetcheckout Physical PoS'),
            ('jetcheckout_link', 'Jetcheckout Payment Link'),
        ]

    @api.model
    def _set_url(self, url):
        try:
            url = urlparse(url)
            return '%s://%s' % (url.scheme, url.netloc)
        except:
            raise ValidationError(_('URL you entered seems mistyped'))

    @api.model
    def create(self, vals):
        if 'jetcheckout_link_url' in vals:
            vals['jetcheckout_link_url'] = self._set_url(vals['jetcheckout_link_url'])
        return super().create(vals)

    def write(self, vals):
        if 'jetcheckout_link_url' in vals:
            vals['jetcheckout_link_url'] = self._set_url(vals['jetcheckout_link_url'])
        return super().write(vals)

    def action_acquirer_jetcheckout(self):
        self.ensure_one()
        acquirer = self.env['payment.acquirer']._get_acquirer(providers=['jetcheckout'], limit=1)
        action = self.env.ref('payment.action_payment_acquirer').read()[0]
        action['views'] = [(False, 'form')]
        if not acquirer:
            action['context'] = {'default_provider': 'jetcheckout'}
        else:
            action['res_id'] = acquirer.id
        return action


class PosPaymentMethodPhysicalSingle(models.Model):
    _name = 'pos.payment.method.physical.single'
    _description = 'Physical PoS for Single Payments'

    config_id = fields.Many2one('pos.config')
    name = fields.Char()


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    payment_transaction_id = fields.Many2one('payment.transaction', string='Transaction', copy=False, readonly=True)

    @api.model
    def create(self, values):
        if 'transaction_id' in values:
            try:
                values['payment_transaction_id'] = int(values['transaction_id'])
            except:
                pass
        res = super().create(values)
        res.payment_transaction_id.pos_payment_id = res.id
        return res

    def name_get(self):
        res = []
        for payment in self:
            res.append((payment.id, '%s #%s' % (payment.session_id.name or _('Payment'), payment.id)))
        return res


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _compute_transaction_count(self):
        for order in self:
            order.transaction_count = len(order.transaction_ids)

    transaction_ids = fields.One2many('payment.transaction', 'pos_order_id', string='Transactions', copy=False)
    transaction_count = fields.Integer(compute='_compute_transaction_count')

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        if ui_order['transaction_ids']:
            res['transaction_ids'] = [(4, id) for id in ui_order['transaction_ids']]
        return res

    def action_view_transactions(self):
        self.ensure_one()
        action = self.env.ref('payment.action_payment_transaction').read()[0]
        action['domain'] = [('pos_order_id', '=', self.id)]
        return action


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _create_split_account_payment(self, payment, amounts):
        payment_method = payment.payment_method_id
        if not payment_method.use_payment_terminal or payment_method.use_payment_terminal not in ('jetcheckout_virtual', 'jetcheckout_physical', 'jetcheckout_link'):
            return super()._create_split_account_payment(payment, amounts)

        transaction = payment.payment_transaction_id
        if not transaction:
            return self.env['account.move.line']

        journal_line = transaction.acquirer_id._get_journal_line(transaction.jetcheckout_vpos_name, transaction.jetcheckout_vpos_ref)
        journal_id = journal_line.journal_id or payment_method.journal_id
        if not journal_id:
            return self.env['account.move.line']

        outstanding_account = payment_method.outstanding_account_id or journal_id.default_account_id
        accounting_partner = self.env['res.partner']._find_accounting_partner(payment.partner_id)
        destination_account = accounting_partner.property_account_receivable_id

        if float_compare(amounts['amount'], 0, precision_rounding=self.currency_id.rounding) < 0:
            outstanding_account, destination_account = destination_account, outstanding_account

        account_payment = transaction.with_context(journal_line=journal_line, no_terms=True)._jetcheckout_payment({
            'amount': abs(amounts['amount']),
            'partner_id': payment.partner_id.id,
            'journal_id': journal_id.id,
            'force_outstanding_account_id': outstanding_account.id,
            'destination_account_id': destination_account.id,
            'ref': _('%s POS payment of %s in %s') % (payment_method.name, payment.partner_id.display_name, self.name),
            'pos_payment_method_id': payment_method.id,
            'pos_session_id': self.id,
        })
        return account_payment.move_id.line_ids.filtered(lambda line: line.account_id == account_payment.destination_account_id)