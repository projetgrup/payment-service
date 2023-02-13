# -*- coding: utf-8 -*-
import itertools
from odoo import models, api, fields


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', domain="[('warehouse_id', '=', id), ('warehouse_id.company_id', '=', company_id)]", ondelete='restrict')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transfer_method = fields.Selection([
        ('shopping', 'Shopping'),
        ('cargo_paid', 'Paid Cargo'),
        ('cargo_free', 'Free Cargo'),
        ('vehicle', 'Vehicle')
    ], string='Transfer Method', readonly=True)

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        values = self.env.context.get('pos_line_values', {}).get('transfer_values')
        if values:
            for line in lines:
                vals = self._prepare_stock_move_vals(line, line)
                are_qties_done = True
                if line.id in values:
                    are_qties_done = values[line.id]['done']
                    if values[line.id]['date']:
                        vals['date'] = values[line.id]['date']
                        vals['date_deadline'] = values[line.id]['date']

                move = self.env['stock.move'].create(vals)
                move = move._action_confirm()
                move._add_mls_related_to_order(lines, are_qties_done=are_qties_done)
        else:
            super(StockPicking, self)._create_move_from_pos_order_lines(lines)

    def _action_done(self):
        values = self.env.context.get('pos_line_values', {}).get('transfer_values')
        if values and any(not value['done'] for value in values.values()):
            return True
        return super(StockPicking, self)._action_done()

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        locations = lines.mapped('location_id').ids
        transfers = list(set(lines.mapped('transfer_method')))

        header = []
        items = []
        if locations:
            items.append(locations)
            header.append('location_id')
        if transfers:
            items.append(transfers)
            header.append('transfer_method')
        items = list(itertools.product(*items))
        if not items:
            return super(StockPicking, self)._create_picking_from_pos_order_lines(location_dest_id, lines, picking_type, partner=partner)

        pickings = self.env['stock.picking']
        warehouses = self.env['stock.warehouse'].sudo()
        for item in items:
            values = dict(zip(header, item))
            orderlines = lines.filtered(lambda l: l.location_id.id == values.get('location_id') and l.transfer_method == values.get('transfer_method'))
            values['transfer_values'] = {
                orderline.id: {
                    'date': orderline.transfer_date,
                    'done': orderline.transfer_type == 'immediately',
                } for orderline in orderlines
            }

            warehouse = warehouses.search([('lot_stock_id', '=', values.get('location_id'))], limit=1)
            picking_type = warehouse and warehouse.picking_type_id or picking_type
            pickings |= super(StockPicking, self.with_context(pos_line_values=values))._create_picking_from_pos_order_lines(location_dest_id, orderlines, picking_type, partner=partner)
        return pickings

    @api.model
    def create(self, values):
        vals = self.env.context.get('pos_line_values')
        if vals:
            if 'location_id' in vals:
                values['location_id'] = vals['location_id']
            if 'transfer_method' in vals:
                values['transfer_method'] = vals['transfer_method']
        return super(StockPicking, self).create(values)
