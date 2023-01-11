# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
    def _set_link_url(self, url):
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


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _compute_transaction_count(self):
        for order in self:
            order.transaction_count = len(order.transaction_ids)

    transaction_ids = fields.One2many('payment.transaction', 'pos_order_id', string='Transactions', copy=False)
    transaction_count = fields.Integer(compute='_compute_transaction_count')

    @api.model
    def _process_order(self, order, draft, existing_order):
        res = super()._process_order(order, draft, existing_order)
        pos_order = self.browse(res)
        transaction_ids =  order['data']['transaction_ids']
        if transaction_ids:
            pos_order.transaction_ids = [(4, id) for id in transaction_ids]
        return res

    def action_view_transactions(self):
        self.ensure_one()
        action = self.env.ref('payment.action_payment_transaction').read()[0]
        action['domain'] = [('pos_order_id', '=', self.id)]
        return action
