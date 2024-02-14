# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from odoo.http import route, request, Response, Controller


class PaymentSaleController(Controller):

    @route('/my/order', type='json', auth='public', website=True)
    def page_order_save(self, values):
        token = urlparse(request.httprequest.referrer).path.rsplit('/', 1).pop()
        pid, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not pid or not token:
            raise

        company = request.env.company
        if not company.system:
            raise

        partner = request.env['res.partner'].sudo().search([
            ('id', '=', pid),
            ('access_token', '=', token),
            ('company_id', '=', company.id),
        ], limit=1)
        if not partner:
            raise

        vals = {}
        if 'lines' in values:
            vals['order_line'] = [(5, 0, 0)] + [(0, 0, {
                'product_id': line['pid'],
                'product_uom_qty': line['qty'],
                'paylox_system_price_unit': line['price'],
            }) for line in values['lines']]
            vals['state'] = 'draft'
        if 'lock' in values:
            vals['state'] = 'sent'

        order = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('company_id', '=', company.id),
            ('state', 'in', ('draft', 'sent')),
        ], limit=1)
        if not order:
            order = request.env['sale.order'].sudo().create({
                'partner_id': partner.id,
                'company_id': company.id,
                'system': company.system,
                **vals
            })
        else:
            order.write(vals)

        return True
