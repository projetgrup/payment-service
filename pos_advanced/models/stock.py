# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    _inherit='stock.picking'

    def _prepare_picking_vals(self, partner, picking_type, location_id, location_dest_id):
        res = super(StockPicking, self)._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
        partner_shipping_id = self.env.context.get('partner_shipping_id')
        if partner_shipping_id:
            res['partner_id'] = partner_shipping_id.id
        return res
