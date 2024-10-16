# -*- coding: utf-8 -*-
import re
import werkzeug

from odoo import _
from odoo.http import route, request
from odoo.exceptions import ValidationError
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller


class CustomerPortal(portal.CustomerPortal):

    @route(['/my', '/my/home'], type='http', auth='user', website=True, sitemap=False)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'insurance':
            return request.redirect('/my/payment')
        return super().home(**kwargs)


class PayloxSystemInsuranceController(Controller):

    def _get_data_values(self, data, **kwargs):
        values = super()._get_data_values(data, **kwargs)
        if request.env.company.system == 'insurance':
            partner = self._get_partner(kwargs['partner'], parent=True)
            reference = partner.bank_ids and partner.bank_ids[0]['api_ref']
            if not reference:
                raise ValidationError(_('%s must have at least one bank account which is verified.' % partner.name))
            values.update({
                'is_submerchant_payment': True,
                'submerchant_external_id': reference,
                'submerchant_price': data['amount']/100,
            })
            if not kwargs.get('verify'):
                values.update({
                    'is_3d': False,
                })
        return values
