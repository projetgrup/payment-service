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
            items = kwargs.get('items', [])
            ids = [i for i, null in items]
            item = {item.id: {'ref': item.ref, 'advance': item.advance} for item in request.env['payment.item'].sudo().browse(ids)}
            res['paylox_transaction_item_ids'] = [(0, 0, {
                'item_id': id,
                'amount': amount,
                'ref': item[id]['ref'],
                'advance': item[id]['advance'],
            }) for id, amount in items]
        return res

    def _prepare_system(self, company, system, partner, transaction, options={}):
        options['no_compute_payment_tags'] = True
        res = super()._prepare_system(company, system, partner, transaction, options=options)
        if system == 'vendor':
            try:
                wizard = request.env['syncops.sync.wizard'].sudo().create({
                    'type': 'item',
                    'system': 'vendor',
                    'type_item_subtype': company.syncops_sync_item_subtype,
                })
                wizard.with_context(partner=partner).confirm()
                wizard.with_context(wizard_id=wizard.id, partner=partner).sync()
            except:
                pass

        campaign = res['campaign']
        payments, payment_tags = partner._get_payments()
        if payment_tags and payment_tags[0].campaign_id:
            campaign = payment_tags[0].campaign_id.name
            raise Exception(campaign)

        res.update({
            'campaign': campaign,
            'payments': payments,
            'payment_tags': payment_tags,
        })
        return res
