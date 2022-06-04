# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


class VendorPaymentController(JetController):

    def _jetcheckout_tx_vals(self, **kwargs):
        res = super()._jetcheckout_tx_vals(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'vendor':
            pass
        return res

    def _jetcheckout_system_page_values(self, company, system, parent, transaction):
        res = super()._jetcheckout_system_page_values(company, system, parent, transaction)
        if system == 'vendor':
            pass
        return res
