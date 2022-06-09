# -*- coding: utf-8 -*-
from odoo.http import route, request
from odoo.addons.payment_jetcheckout_system.controllers.main import JetcheckoutSystemController as JetSystemController
from odoo.addons.portal.controllers import portal

class CustomerPortal(portal.CustomerPortal):
    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'vendor':
            return request.redirect('/my/payment')
        return super().home(**kwargs)

#class VendorPaymentController(JetSystemController):

    #def _jetcheckout_tx_vals(self, **kwargs):
    #    res = super()._jetcheckout_tx_vals(**kwargs)
    #    system = kwargs.get('system', request.env.company.system)
    #    if system == 'vendor':
    #        pass
    #    return res

    #def _jetcheckout_system_page_values(self, company, system, parent, transaction):
    #    res = super()._jetcheckout_system_page_values(company, system, parent, transaction)
    #    if system == 'vendor':
    #        pass
    #    return res
