# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PaymentProduct(models.AbstractModel):
    _inherit = 'payment.product'


    @api.model
    def show_buttons(self):
        if self.env.company.system == 'jewelry':
            return {
                'show_update_price_button': self.env['syncops.connector'].sudo().count('product_get_prices'),
                'show_update_product_button': self.env['syncops.connector'].sudo().count('product_get_products'),
            }
        return super().show_buttons()

    @api.model
    def update_price(self):
        company = self.env.company
        if company.system == 'jewelry':
            prices, message = self.env['syncops.connector'].sudo()._execute('product_get_prices', company=company, message=True)
            if prices is None:
                return {'error': _('An error occured:\n%s') % message}

            prices = {p['code']: p['price'] for p in prices}
            products = self.env['product.product'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('default_code', 'in', list(prices.keys())),
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

    @api.model
    def update_product(self):
        company = self.env.company
        if company.system == 'jewelry':
            prods, message = self.env['syncops.connector'].sudo()._execute('product_get_products', company=company, message=True)
            if prods is None:
                return {'error': _('An error occured:\n%s') % message}

            def _weight(w):
                w = int(w) == w and int(w) or w
                return str(w)

            types = {}
            categs = set()
            brands = set()
            weights = set()
            for prod in prods:
                prod['purity'] = '995'
                prod['weight'] = _weight(prod['weight'])
                if not prod['type']:
                    prod['type'] = 'Other'
                elif prod['type'] == 'Bars':
                    weights.add(prod['weight'])

                brands.add(prod['provider'])
                categs.add(prod['type'])

                if prod['type'] not in types:
                    types[prod['type']] = {'brand': set(), 'weight': set(), 'purity': set()}
                if prod['type'] == 'Bars':
                    types[prod['type']]['weight'].add(prod['weight'])
                types[prod['type']]['brand'].add(prod['provider'])
                types[prod['type']]['purity'].add(prod['purity'])

            categs_all = self.env['product.category'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
            ])
            for categ in categs:
                if categ not in categs_all.mapped('name'):
                    categs_all |= categs_all.create({
                        'name': categ,
                        'view_type': 'list',
                    })

            brands_id = self.env['product.attribute'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('payment_type', '=', 'brand'),
            ], limit=1)
            brands_all = self.env['product.attribute.value'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('attribute_id', '=', brands_id.id),
            ])
            for brand in brands:
                if brand not in brands_all.mapped('name'):
                    brands_all |= brands_all.create({
                        'attribute_id': brands_id.id,
                        'name': brand
                    })

            weights_id = self.env['product.attribute'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('payment_type', '=', 'weight'),
            ], limit=1)
            weights_all = self.env['product.attribute.value'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('attribute_id', '=', weights_id.id),
            ])
            for weight in weights:
                if weight not in weights_all.mapped('name'):
                    weights_all |= weights_all.create({
                        'attribute_id': weights_id.id,
                        'name': weight
                    })

            purities_id = self.env['product.attribute'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('payment_type', '=', 'purity'),
            ], limit=1)
            purities_all = self.env['product.attribute.value'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('attribute_id', '=', purities_id.id),
            ])

            attributes = {
                'brand': {brand.name: brand.id for brand in brands_all},
                'weight': {weight.name: weight.id for weight in weights_all},
                'purity': {purity.name: purity.id for purity in purities_all},
            }

            products_all = self.env['product.template'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
            ])
            names_all = []
            for prod in prods:
                if prod['type'] == 'Bars':
                    name = '%s %s' % (prod['type'], prod['metal'])
                    if name in names_all:
                        continue
                    names_all.append(name)
                    product = products_all.filtered(lambda p: p.name == name)
                else:
                    name = prod['name']
                    product = products_all.filtered(lambda p: p.default_code == prod['code'])

                categ = categs_all.filtered(lambda c: c.name == prod['type'])

                if not product:
                    attribute_line_ids = [(0, 0, {
                        'attribute_id': brands_id.id,
                        'value_ids': [(4, attributes['brand'][name]) for name in types[prod['type']]['brand']]
                    })]
                    if prod['type'] == 'Bars':
                        attribute_line_ids.extend([(0, 0, {
                            'attribute_id': weights_id.id,
                            'value_ids': [(4, attributes['weight'][name]) for name in types[prod['type']]['weight']]
                        })] + [(0, 0, {
                            'attribute_id': purities_id.id,
                            'value_ids': [(4, attributes['purity'][name]) for name in types[prod['type']]['purity']]
                        })])

                    values = {
                        'name': name,
                        'categ_id': categ.id,
                        'payment_page_ok': True,
                        'payment_price_flow': True,
                        'default_code': prod['code'],
                        'detailed_type': 'consu',
                        'payment_price_method': 'formula',
                        'attribute_line_ids': attribute_line_ids,
                    }
                    if prod['metal'] == 'Gold':
                        values.update({
                            'payment_color_foreground': '#000000',
                            'payment_color_background': '#F1C332',
                        })
                    elif prod['metal'] == 'Silver':
                        values.update({
                            'payment_color_foreground': '#000000',
                            'payment_color_background': '#F3F3F3',
                        })
                    products_all |= products_all.create(values)

                else:
                    attribute_brand_id = product.attribute_line_ids.filtered(lambda a: a.attribute_id.id == brands_id.id)
                    attribute_weight_id = product.attribute_line_ids.filtered(lambda a: a.attribute_id.id == weights_id.id)
                    attribute_purity_id = product.attribute_line_ids.filtered(lambda a: a.attribute_id.id == purities_id.id)                    

                    attribute_line_ids = [(
                        attribute_brand_id and 1 or 0,
                        attribute_brand_id.id or 0,
                        {
                            'attribute_id': brands_id.id,
                            'value_ids': [(4, attributes['brand'][name]) for name in types[prod['type']]['brand']],
                        }
                    )]
                    if prod['type'] == 'Bars':
                        attribute_line_ids.extend([(
                            attribute_weight_id and 1 or 0,
                            attribute_weight_id.id or 0,
                            {
                                'attribute_id': weights_id.id,
                                'value_ids': [(4, attributes['weight'][name]) for name in types[prod['type']]['weight']],
                            }
                        ), (
                            attribute_purity_id and 1 or 0,
                            attribute_purity_id.id or 0,
                            {
                                'attribute_id': purities_id.id,
                                'value_ids': [(4, attributes['purity'][name]) for name in types[prod['type']]['purity']],
                            }
                        )])

                    values = {
                        'payment_page_ok': True,
                        'attribute_line_ids': attribute_line_ids,
                    }
                    if prod['type'] == 'Bars':
                        values['default_code'] = False
                    product.write(values)

            products = self.env['product.product'].sudo().with_context(no_broadcast=True).search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
            ])
            base_gold = self.env['product.template'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('default_code', '=', 'XAUTRY'),
            ], limit=1)
            base_silver = self.env['product.template'].sudo().search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('default_code', '=', 'XAGTRY'),
            ], limit=1)

            tuple_keys = [] #TODO
            for prod in prods:
                if prod['type'] == 'Bars':
                    product = products.filtered(lambda p: p.default_code == prod['code'])
                    values = {
                        'payment_page_ok': True,
                        'payment_pid': prod['id'],
                        'payment_name': prod['name'],
                        'weight': float(prod['weight']),
                    }
                    if prod['metal'] == 'Gold':
                        values['payment_price_method_product_id'] = base_gold.id
                        values['payment_price_method_formula'] = 'x*%s' % prod.get('base', '1')
                    elif prod['metal'] == 'Silver':
                        values['payment_price_method_product_id'] = base_silver.id
                        values['payment_price_method_formula'] = 'x*%s' % prod.get('base', '1')

                    if product:
                        template = product.product_tmpl_id
                    else:
                        name = '%s %s' % (prod['type'], prod['metal'])
                        template = products_all.filtered(lambda p: p.name == name)

                    attribute_value_ids = [
                        attributes['brand'][prod['provider']],
                        attributes['weight'][prod['weight']],
                        attributes['purity'][prod['purity']],
                    ]

                    #TODO Block starts
                    tuple_key = [template.id] + attribute_value_ids
                    if tuple_key in tuple_keys:
                        prod['purity'] = '999'
                        attribute_value_ids[2] = attributes['purity'][prod['purity']]

                    tuple_key[3] = attribute_value_ids[2]
                    if tuple_key in tuple_keys:
                        prod['purity'] = '991'
                        attribute_value_ids[2] = attributes['purity'][prod['purity']]
                    tuple_keys.append(tuple_key)
                    #TODO Block ends

                    attribute_values = self.env['product.template.attribute.value'].sudo().search([
                        ('attribute_id.system', '=', 'jewelry'),
                        ('attribute_id.company_id', '=', company.id),
                        ('product_tmpl_id', '=', template.id),
                        ('product_attribute_value_id', 'in', attribute_value_ids),
                    ])
                    values['product_template_attribute_value_ids'] = [(6, 0, attribute_values.ids)]

                    if product:
                        product.write(values)
                        products -= product
                    else:
                        products.create({
                            'product_tmpl_id': template.id,
                            'default_code': prod['code'],
                            **values
                        })
                else:
                    product = products.filtered(lambda p: p.product_tmpl_id.default_code == prod['code'])
                    values = {
                        'payment_page_ok': True,
                        'payment_pid': prod['id'],
                        'payment_name': prod['name'],
                        'default_code': prod['code'],
                        'weight': float(prod['weight']),
                    }
                    if product:
                        product.write(values)
                        products -= product
                    else:
                        template = products_all.filtered(lambda p: p.default_code == prod['code'])

                        attribute_value_ids = [
                            attributes['brand'][prod['provider']],
                        ]

                        attribute_values = self.env['product.template.attribute.value'].sudo().search([
                            ('attribute_id.system', '=', 'jewelry'),
                            ('attribute_id.company_id', '=', company.id),
                            ('product_tmpl_id', '=', template.id),
                            ('product_attribute_value_id', 'in', attribute_value_ids),
                        ])
                        values['product_template_attribute_value_ids'] = [(6, 0, attribute_values.ids)]

                        products.create({
                            'product_tmpl_id': template.id,
                            'name': prod['name'],
                            **values
                        })

            products.write({
                'payment_page_ok': False,
            })
            return {}
        return super().update_product()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])


class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])
    payment_type = fields.Selection(selection_add=[
        ('weight', 'Weight'),
        ('purity', 'Purity'),
    ])
