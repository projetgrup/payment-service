# -*- coding: utf-8 -*-
from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        if self.currency_id:
            for line in self.invoice_line_ids:
                from_currency = None
                price_unit = line.price_unit
                if line.payment_subscription_id:
                    for i in line.payment_subscription_id.line_ids:
                        if i.product_id == line.product_id and i.display_name == line.display_name and i.quantity == line.quantity and i.uom_id == line.product_uom_id:
                            price_unit = i.price_unit
                            from_currency = line.payment_subscription_id.currency_id
                if from_currency:
                    line.price_unit = from_currency.with_context(date=self.invoice_date).compute(price_unit, self.currency_id, round=False)
