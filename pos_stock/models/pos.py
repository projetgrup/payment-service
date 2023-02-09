# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    picking_state = fields.Boolean('Ready State')
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

    def _create_order_picking(self):
        self.ensure_one()

        if not self.session_id.update_stock_at_closing or (self.company_id.anglo_saxon_accounting and self.to_invoice):
            picking_type_id = self.config_id.picking_type_id

            if self.partner_id.property_stock_customer:
                location_dest_id = self.partner_id.property_stock_customer.id
            elif not picking_type_id or not picking_type_id.default_location_dest_id:
                location_dest_id = self.env['stock.warehouse']._get_partner_locations()[0].id
            else:
                location_dest_id = picking_type_id.default_location_dest_id.id

            pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(location_dest_id, picking_type_id, self.lines, self.partner_id)
            if pickings:
                if type(pickings) == list:
                    for each_picking in pickings:
                        each_picking.write({
                            'pos_session_id': self.session_id.id,
                            'pos_order_id': self.id,
                            'origin': self.name
                        })
                else:
                    pickings.write({
                        'pos_session_id': self.session_id.id,
                        'pos_order_id': self.id,
                        'origin': self.name
                    })


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

        if orderline.location_id:
            res['location_id'] = orderline.location_id.id

        if orderline.transfer_date:
            res['transfer_date'] = orderline.transfer_date

        if orderline.transfer_type:
            res['transfer_type'] = orderline.transfer_type

        if orderline.transfer_location:
            res['transfer_location'] = orderline.transfer_location

        return res

    @api.model
    def _order_line_fields(self, line, session_id=None):
        #line[2]['location_id'] = line[2]['location_id'] #TODO interesting
        res = super(PosOrderLine, self)._order_line_fields(line, session_id)
        if line[2].get('refunded_orderline_id'):
            orderline = self.search([('id', '=', line[2].get('refunded_orderline_id'))])
            if orderline:
                if orderline.location_id:
                    res[2]['location_id'] = orderline.location_id.id
                if orderline.transfer_date:
                    res[2]['transfer_date'] = orderline.transfer_date
                if orderline.transfer_type:
                    res[2]['transfer_type'] = orderline.transfer_type
                if orderline.transfer_type:
                    res[2]['transfer_location'] = orderline.transfer_location
        return res


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _create_picking_at_end_of_session(self):
        self.ensure_one()

        lines_grouped_by_dest_location = {}
        picking_type_id = self.config_id.picking_type_id

        if not picking_type_id or not picking_type_id.default_location_dest_id:
            session_destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
        else:
            session_destination_id = picking_type_id.default_location_dest_id.id

        for order in self.order_ids:
            if order.company_id.anglo_saxon_accounting and order.to_invoice:
                continue

            destination_id = order.partner_id.property_stock_customer.id or session_destination_id
            if destination_id in lines_grouped_by_dest_location:
                lines_grouped_by_dest_location[destination_id] |= order.lines
            else:
                lines_grouped_by_dest_location[destination_id] = order.lines

        for location_dest_id, lines in lines_grouped_by_dest_location.items():
            pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(location_dest_id, picking_type_id, lines, False)
            if pickings:
                if type(pickings) == list:
                    for each_picking in pickings:
                        each_picking.write({'pos_session_id': self.id, 'origin': self.name})
                else:
                    pickings.write({'pos_session_id': self.id, 'origin': self.name})
