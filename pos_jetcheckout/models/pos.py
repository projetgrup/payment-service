# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class PosConfig(models.Model):
    _inherit = 'pos.config'

    jetcheckout_link_duration = fields.Integer(string='Payment Link Lifetime', default=300)
    jetcheckout_branch_code = fields.Char(string='Store Code')

    @api.constrains('jetcheckout_link_duration')
    def _check_link_duration(self):
        for config in self:
            if not config.jetcheckout_link_duration > 0:
                raise ValidationError(_('Payment link lifetime cannot be lower than zero'))


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    @api.depends('type')
    def _compute_hide_use_payment_terminal(self):
        no_terminals = not bool(self._fields['use_payment_terminal'].selection(self))
        for payment_method in self:
            payment_method.hide_use_payment_terminal = no_terminals or payment_method.type == 'cash'

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
            vals['jetcheckout_link_url'] = self._set_link_url(vals['jetcheckout_link_url'])
        return super().create(vals)

    def write(self, vals):
        if 'jetcheckout_link_url' in vals:
            vals['jetcheckout_link_url'] = self._set_link_url(vals['jetcheckout_link_url'])
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

    def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        data = super()._create_account_move(balancing_account=balancing_account, amount_to_balance=amount_to_balance, bank_payment_method_diffs=bank_payment_method_diffs)
        #_logger.error(self.env['pos.payment'].sudo().search([('session_id', '=', self.id)]))
        #_logger.error(data)
        return data

    def _compute_transaction_count(self):
        for order in self:
            order.transaction_count = len(order.transaction_ids)
