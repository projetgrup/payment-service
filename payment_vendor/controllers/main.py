# -*- coding: utf-8 -*-
from odoo.http import route, request
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller


class CustomerPortal(portal.CustomerPortal):
    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'vendor':
            return request.redirect('/my/payment')
        return super().home(**kwargs)


class PayloxSystemVendorController(Controller):

    def _get_tx_vals(self, **kwargs):
        res = super()._get_tx_vals(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'vendor':
            ids = 'jetcheckout_item_ids' in res and res['jetcheckout_item_ids'][0][2] or False
            if ids:
                payment_ids = request.env['payment.item'].sudo().browse(ids)
                for payment in payment_ids:
                    payment.paid_amount = payment.amount
        return res

    def _prepare_system(self, company, system, partner, transaction):
        res = super()._prepare_system(company, system, partner, transaction)
        if system == 'vendor':
            wizard = request.env['syncops.connector'].create({
                'type': 'item',
                'system': 'vendor',
                'type_item_subtype': company.syncops_sync_item_subtype,
            })
            wizard.with_context(partner=partner).confirm()
            wizard.with_context(partner=partner).sync()
        return res
