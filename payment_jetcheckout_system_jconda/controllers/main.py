# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


class JetcheckoutSystemController(JetController):

    def _jetcheckout_get_data(self, acquirer=False, company=False, transaction=False, balance=True):
        values = super()._jetcheckout_get_data(acquirer=acquirer, company=company, transaction=transaction, balance=balance)
        try:
            result = request.env['jconda.connector'].sudo().execute('partner_balance', values['partner'], values['company'].id)
            balances = []
            for res in result:
                balances.append({
                    'amount': res['amount'],
                    'currency': request.env['res.currency'].sudo().with_context(active_test=False).search([('name', '=', res['currency'])], limit=1)
                })
            values['balances'] = balances
            values['show_balance'] = True
        except:
            values['show_balance'] = False
        return values
