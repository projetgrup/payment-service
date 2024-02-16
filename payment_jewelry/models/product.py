# -*- coding: utf-8 -*-
import logging

import odoo
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PaymentProduct(models.AbstractModel):
    _inherit = 'payment.product'


    @api.model
    def show_buttons(self):
        if self.env.company.system == 'jewelry':
            return {
                'show_update_price_button': self.env['syncops.connector'].sudo().count('product_get_products')
            }
        return super().show_buttons()

    @api.model
    def update_price(self):
        company = self.env.company
        if company.system == 'jewelry':
            prices, message = self.env['syncops.connector'].sudo()._execute('product_get_products', company=company, message=True)
            if prices is None:
                return {'error': message}

            prices = {p['code']: p['price'] for p in prices}
            products = self.env['product.product'].sudo().search([
                ('company_id', '=', company.id),
                ('system', '=', 'jewelry'),
            ])
            for product in products:
                try:
                    product.with_context(no_broadcast=True).write({
                        'price': prices[product.default_code],
                    })
                except:
                    continue

            self.broadcast_price(products)
            return {}
        return super().update_price()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])


class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])
    payment_type = fields.Selection(selection_add=[('weight', 'Weight')])
