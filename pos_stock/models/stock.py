# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.tools import float_is_zero
from odoo.exceptions import UserError, ValidationError


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', domain="[('warehouse_id', '=', id), ('warehouse_id.company_id', '=', company_id)]", ondelete='restrict')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transfer_location = fields.Char(string='Transfer Location')

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, picking_type_id, lines, partner):
        pickings = self.env['stock.picking']
        lines = lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding))
        if not lines:
            return pickings

        lines_available = lines.filtered(lambda l: l.qty > 0)
        lines_absent = lines - lines_available

        picking_list = []
        if lines_available:
            location_list = []
            location_id = picking_type_id.default_location_src_id.id

            for line in lines_available.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
                if line.location_id.id and int(line.location_id.id) not in location_list:
                    location_list.append(int(line.location_id.id))

            for location in location_list:
                warehouse = self.env['stock.warehouse'].sudo().search([('lot_stock_id', '=', int(location))], limit=1)
                type_id = warehouse and warehouse.picking_type_id and warehouse.picking_type_id or picking_type_id

                def create_stock_move(order_lines, immediately=False):
                    picking = self.env['stock.picking'].create(self._prepare_picking_vals(partner, type_id, location, location_dest_id))

                    if not immediately:
                        transfer_location = [dict(line._fields['transfer_location']._description_selection(self.env)).get(line.transfer_location) for line in order_lines]
                        transfer_location = set(transfer_location)
                        picking.transfer_location = ','.join(transfer_location)

                    for line in order_lines:
                        picking.with_context(immediately=immediately)._create_move_from_pos_order_lines(line)
                        picking_list.append(picking)
                        try:
                            picking_state = line.order_id.config_id.picking_state
                            with self.env.cr.savepoint():
                                if immediately and not picking_state:
                                    picking._action_done()
                                else:
                                    if picking:
                                        for line in picking.move_line_ids:
                                            line.qty_done = 0
                        except (UserError, ValidationError):
                            pass

                    if not immediately:
                        from datetime import date, datetime
                        transfer_date = max(d.transfer_date for d in order_lines if isinstance(d.transfer_date, date))
                        if transfer_date:
                            transfer_date = datetime.combine(transfer_date, datetime.min.time())
                            picking.write({'scheduled_date': transfer_date})

                line_immediately = []
                line_carrying = []
                line_later = []

                for line in lines_available.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
                    if (int(line.location_id.id) != location):
                        continue

                    if line.transfer_type in [False, 'immediately']:
                        line_immediately.append(line)
                        continue

                    if line.transfer_type in ['later'] and line.transfer_location != 'shopping':
                        line_carrying.append(line)
                        continue

                    if line.transfer_type in ['later'] and line.transfer_location == 'shopping':
                        line_later.append(line)
                        continue

                if line_immediately:
                    create_stock_move(line_immediately, True, False)

                if line_later:
                    create_stock_move(line_later, False, False)

                if line_carrying:
                    create_stock_move(line_carrying, False, True)

            if not location_list:
                self.env['stock.picking'].create(self._prepare_picking_vals(partner, picking_type_id, location_id, location_dest_id))

        if lines_absent:
            for line in lines_absent:
                if picking_type_id.return_picking_type_id:
                    return_picking_type = picking_type_id.return_picking_type_id
                    return_location_id = return_picking_type.default_location_dest_id.id
                else:
                    return_picking_type = picking_type_id
                    return_location_id = line.location_id.id

                negative_picking = self.env['stock.picking'].create(self._prepare_picking_vals(partner, return_picking_type, location_dest_id, return_location_id))
                negative_picking._create_move_from_pos_order_lines(line)
                picking_list.append(negative_picking)
                try:
                    with self.env.cr.savepoint():
                        negative_picking._action_done()
                except (UserError, ValidationError):
                    pass
        return picking_list


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _add_mls_related_to_order(self, related_order_lines, are_qties_done=True):
        if not self.env.context.get('immediately', False):
            return super(StockMove, self)._add_mls_related_to_order(related_order_lines, False)
        return super(StockMove, self)._add_mls_related_to_order(related_order_lines, are_qties_done)
