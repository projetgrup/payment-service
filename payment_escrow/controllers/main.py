# -*- coding: utf-8 -*-
from odoo import _
from odoo.http import route, request
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller


class CustomerPortal(portal.CustomerPortal):

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            return request.redirect('/my/payment')
        return super().home(**kwargs)


class PayloxSystemEscrowController(Controller):

    def _get_tx_values(self, **kwargs):
        return {
            'paylox_description': kwargs.get('description', False),
            'jetcheckout_payment_ok': kwargs.get('payment_ok', True),
        }

    def _get_tx_values(self, **kwargs):
        res = super()._get_tx_values(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            res.update({
                'jetcheckout_approval_ok': True,
            })
        return res

    def _get_data_values(self, data, transaction, **kwargs):
        values = super()._get_data_values(data, transaction, **kwargs)
        if transaction and transaction.system == 'escrow':
            partner = transaction.paylox_product_ids[0]['product_id']['owner_id']
            reference = partner.bank_ids and partner.bank_ids[0]['api_ref']
            if not reference:
                raise ValidationError(_('%s must have at least one bank account which is verified.' % partner.name))

            if transaction.company_id.payment_page_token_wo_commission:
                amount = float_round(transaction.amount * (1 - (transaction.jetcheckout_commission_rate / 100)), 4)
            else:
                amount = float(kwargs['amount'])

            values.update({
                'is_submerchant_payment': True,
                'submerchant_external_id': reference,
                'submerchant_price': amount,
            })
        return values