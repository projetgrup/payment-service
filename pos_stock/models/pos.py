# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    picking_negative_ok = fields.Boolean('Enable Negative Selling')
    picking_day_threshold = fields.Integer('Threshold After Transfer')
    picking_type = fields.Selection([
        ('quantity_available', 'Available Quantity'),
        ('quantity_unreserved', 'Unreserved Quantity')
    ], string='Picking Type', default='quantity_available', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Default Warehouse', ondelete='restrict')
    warehouse_ids = fields.Many2many('stock.warehouse', 'pos_warehouse_rel', 'pos_id', 'warehouse_id', string='Related Warehouses')


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _process_order(self, order, draft, existing_order):
        res = super(PosOrder, self)._process_order(order, draft, existing_order)
        try:
            now = datetime.now()
            partners = self.env['res.users'].sudo().search([('id', '!=', self.env.uid), ('company_id', '=', self.env.company.id), ('share', '=', False)]).mapped('partner_id')
            messages = [
                [partner, 'pos.bus/all', {
                    'date': now,
                    'type': 'stock',
                    'session': order['data']['pos_session_id'],
                    'cashier': order['data']['pos_uid'],
                    'orders': [{
                        'product': line[2]['product_id'],
                        'location': line[2]['location_id'],
                        'quantity': line[2]['qty'],
                    } for line in order['data']['lines']],
                }
            ] for partner in partners]
            self.env['bus.bus'].with_context(pos=True)._sendmany(messages)
        except:
            pass
        return res


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    location_id = fields.Many2one('stock.location')
    transfer_date = fields.Date('Transfer Date')
    transfer_type = fields.Selection([
        ('immediately', 'Immediately'),
        ('later', 'Later')
    ], string='Transfer Type')
    transfer_location = fields.Selection([
        ('shopping', 'Shopping'),
        ('cargo_paid', 'Paid Cargo'),
        ('cargo_free', 'Free Cargo'),
        ('vehicle', 'Vehicle')
    ], string='Transfer Location')

    def _export_for_ui(self, orderline):
        res = super(PosOrderLine, self)._export_for_ui(orderline)
        res.update({
            'location_id' : orderline.location_id.id,
            'transfer_date' : orderline.transfer_date,
            'transfer_type' : orderline.transfer_type,
            'transfer_location' : orderline.transfer_location,
        })
        return res

    @api.model
    def _order_line_fields(self, line, session_id=None):
        res = super(PosOrderLine, self)._order_line_fields(line, session_id=session_id)
        refunded_orderline = line[2].get('refunded_orderline_id')
        if refunded_orderline:
            orderline = self.search([('id', '=', refunded_orderline)])
            res[2].update({
                'location_id' : orderline.location_id.id,
                'transfer_date' : orderline.transfer_date,
                'transfer_type' : orderline.transfer_type,
                'transfer_location' : orderline.transfer_location,
            })
        return res
