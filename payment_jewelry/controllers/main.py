# -*- coding: utf-8 -*-
from werkzeug.exceptions import NotFound

from odoo.http import route, request
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller


class CustomerPortal(portal.CustomerPortal):
    @route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'jewelry':
            return request.redirect('/my/payment')
        return super().home(**kwargs)


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

    def _prepare_system(self,  company, system, partner, transaction, options={}):
        res = super()._prepare_system(company, system, partner, transaction, options=options)
        if system == 'jewelry':
            products = request.env['product.template'].sudo().with_context(system=system).search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', request.env.company.id),
            ])

            try:
                installment = self._prepare_installment()
                commission = installment['rows'][0]['installments'][0]['crate']
            except:
                commission = 0.0

            res.update({
                'products': products,
                'commission': commission,
            })
        return res

    @route('/my/jewelry/brand', type='json', auth='public', website=True)
    def page_jewelry_brand(self, pid, bid):
        return request.env['product.template'].sudo().with_context(system='jewelry').browse(pid).get_payment_variants('weight', [bid])

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
        result, message = request.env['syncops.connector'].sudo()._execute('partner_get_company', params={'vat': vat}, message=True)
        if result is None:
            return {
                'error': message,
            }
        return result[0]
