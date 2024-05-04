# -*- coding: utf-8 -*-
from werkzeug.exceptions import NotFound

from odoo import _
from odoo.http import route, request
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller


#class CustomerPortal(portal.CustomerPortal):
#    @route(['/my', '/my/home'], type='http', auth='user', website=True)
#    def home(self, **kwargs):
#        system = kwargs.get('system', request.env.company.system)
#        if system == 'jewelry':
#            return request.redirect('/my/payment')
#        return super().home(**kwargs)


class PayloxSystemJewelryController(Controller):

#    @route(['/my/jewelry'], type='http', auth='user', website=True)
#    def page_jewelry(self, **kwargs):
#        system = kwargs.get('system', request.env.company.system)
#        if system == 'jewelry':
#            return request.redirect('/my/payment')
#        return super().home(**kwargs)
#
#    def _get_tx_vals(self, **kwargs):
#        res = super()._get_tx_vals(**kwargs)
#        system = kwargs.get('system', request.env.company.system)
#        if system == 'jewelry':
#            pass
#        return res

    def _prepare_system(self, company, system, partner, transaction, options={}):
        res = super()._prepare_system(company, system, partner, transaction, options=options)
        if system == 'jewelry':
            res.update({
                'currency': company.currency_id,
                'options': {
                    'listen_price_active': True,
                    'save_order_active': True
                },
            })
        return res

    @route(['/my/jewelry/register'], type='http', auth='public', website=True)
    def page_jewelry_register(self, **kwargs):
        system = request.env.company.system
        if system == 'jewelry':
            values = {
                'company': request.env.company,
            }
            return request.render('payment_jewelry.page_regsiter', values)
        raise NotFound()

    @route('/my/jewelry/register/query', type='json', auth='public', website=True)
    def page_jewelry_register_query(self, vat):
        result = request.env['syncops.connector'].sudo()._execute('partner_get_company', params={'vat': vat})
        if result is None:
            return {'error': _('An error occured. Please contact with system administrator.')}
        return result[0]

    @route('/my/product', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_product(self, **kwargs):
        system = request.env.company.system
        if system == 'jewelry':
            raise NotFound()
        return super().page_product(**kwargs)
