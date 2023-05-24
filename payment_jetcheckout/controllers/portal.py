# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.payment.controllers import portal as payment_portal


class PaymentPortal(payment_portal.PaymentPortal):

    def _get_custom_rendering_context_values(self, sale_order_id=None, **kwargs):
        rendering_context_values = super()._get_custom_rendering_context_values(**kwargs)
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            partner = order.partner_invoice_id or order.partner_id
            rendering_context_values['partner_id'] = partner.id
        return rendering_context_values
