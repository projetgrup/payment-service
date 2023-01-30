# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api
from odoo.osv.expression import AND


class PosBank(models.Model):
    _name = 'pos.bank'
    _description = 'Point of Sale - Bank'
    _order = 'sequence'

    config_id = fields.Many2one('pos.config')
    sequence = fields.Integer(default=10)
    logo = fields.Image()
    name = fields.Char(required=True)
    iban = fields.Char(string='IBAN')
    account = fields.Char(string='Account Number')
    branch = fields.Char()
    token = fields.Char(default=lambda self: str(uuid.uuid4()), readonly=True)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    cash_payment_limit_ok = fields.Boolean(string='Limit Cash Payment Amount')
    cash_payment_limit_amount = fields.Monetary(string='Cash Payment Amount Limit')
    bank_ids = fields.One2many('pos.bank', 'config_id', string='Banks')
    bank_ok = fields.Boolean(string='Show Bank Accounts')
    partner_address_state_id = fields.Many2one('res.country.state', string='Default Partner State')
    partner_address_country_id = fields.Many2one('res.country', string='Default Partner Country')
    filter_order_all = fields.Boolean(string='Filter Orders from All Shops', default=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        company = self.env.company
        res['partner_address_state_id'] = company.state_id.id
        res['partner_address_country_id'] = company.country_id.id
        return res

    @api.onchange('partner_address_country_id')
    def onchange_partner_address_country_id(self):
        self.partner_address_state_id = False

class PosOrder(models.Model):
    _inherit = 'pos.order'

    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, copy=False)

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        delivery = ui_order['partner_address']['delivery']
        res['partner_shipping_id'] = delivery and delivery['id'] or False
        return res

    def _create_order_picking(self):
        self.ensure_one()
        if self._should_create_picking_real_time() and self.partner_shipping_id:
            self = self.with_context(partner_shipping_id=self.partner_shipping_id)
        return super(PosOrder, self)._create_order_picking()

    @api.model
    def search_paid_order_ids(self, config_id, domain, limit, offset):
        """
        Get all orders from other shops
        """
        config = self.env['pos.config'].sudo().browse(config_id)
        default_domain = [('state', 'not in', ('draft', 'cancelled'))]
        if not config.filter_order_all:
            default_domain.append(('config_id', '=', config.id))

        real_domain = AND([domain, default_domain])
        ids = self.search(real_domain, limit=limit, offset=offset).ids
        totalCount = self.search_count(real_domain)
        return {'ids': ids, 'totalCount': totalCount}
