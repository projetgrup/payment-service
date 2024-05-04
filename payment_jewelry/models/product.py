# -*- coding: utf-8 -*-

import re
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

            products += products.search([('payment_price_method_product_id', 'in', products.mapped('product_tmpl_id').ids)])
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

            def _provider(p):
                p = p.title()
                return re.sub(r'[^a-zA-Z\s]+', '', p)

            def _purity(p):
                return str(p)

            types = {}
            categs = set()
            brands = set()
            weights = set()
            purities = set()
            for prod in prods:
                prod['purity'] = _purity(prod['purity'])
                prod['weight'] = _weight(prod['weight'])
                prod['provider'] = _provider(prod['provider'])
                if prod['type'] not in ('Bars', 'Coin'):
                    prod['type'] = 'Other'
                elif prod['type'] == 'Bars':
                    weights.add(prod['weight'])

                brands.add(prod['provider'])
                purities.add(prod['purity'])
                categs.add(prod['type'])

                if prod['type'] not in types:
                    types[prod['type']] = {'brand': set(), 'weight': set(), 'purity': set()}
                if prod['type'] == 'Bars':
                    types[prod['type']]['weight'].add(prod['weight'])
                types[prod['type']]['brand'].add(prod['provider'])
                types[prod['type']]['purity'].add(prod['purity'])

            categ_base_gold = self.env['product.category'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('name', '=', 'Base Gold'),
            ], limit=1)
            if not categ_base_gold:
                categ_base_gold = categ_base_gold.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Base Gold',
                    'view_type': 'flex',
                })
            categ_base_silver = self.env['product.category'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('name', '=', 'Base Silver'),
            ], limit=1)
            if not categ_base_silver:
                categ_base_silver = categ_base_silver.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Base Silver',
                    'view_type': 'flex',
                })
            categ_bars = self.env['product.category'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('name', '=', 'Bars'),
            ], limit=1)
            if not categ_bars:
                categ_bars = categ_bars.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Bars',
                    'view_type': 'table',
                })
            categ_coin = self.env['product.category'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('name', '=', 'Bars'),
            ], limit=1)
            if not categ_coin:
                categ_coin = categ_coin.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Coin',
                    'view_type': 'list',
                })
            categs_all = self.env['product.category'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
            ])
            categs_name = categs_all.mapped('name')
            for categ in categs:
                if categ not in categs_name:
                    categs_all |= categs_all.create({
                        'name': categ,
                        'view_type': 'list',
                    })
                    categs_name.append(categ)

            brands_id = self.env['product.attribute'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('payment_type', '=', 'brand'),
            ], limit=1)
            if not brands_id:
                brands_id = brands_id.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Brand',
                    'payment_type': 'brand',
                    'create_variant': 'dynamic',
                })
            brands_name = brands_id.value_ids.mapped('name')
            for brand in brands:
                if brand not in brands_name:
                    brands_id.value_ids = [(0, 0, {'name': brand})]
                    brands_name.append(brand)

            weights_id = self.env['product.attribute'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('payment_type', '=', 'weight'),
            ], limit=1)
            if not weights_id:
                weights_id = weights_id.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Weight',
                    'payment_type': 'weight',
                    'create_variant': 'dynamic',
                })
            weights_name = weights_id.value_ids.mapped('name')
            for weight in weights:
                if weight not in weights_name:
                    weights_id.value_ids = [(0, 0, {'name': weight})]
                    weights_name.append(weight)

            purities_id = self.env['product.attribute'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('payment_type', '=', 'purity'),
            ], limit=1)
            if not purities_id:
                purities_id = purities_id.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Purity',
                    'payment_type': 'purity',
                    'create_variant': 'dynamic',
                })
            purities_name = purities_id.value_ids.mapped('name')
            for purity in purities:
                if purity not in purities_name:
                    purities_id.value_ids = [(0, 0, {'name': purity})]
                    purities_name.append(purity)

            attributes = {
                'brand': {brand.name: brand.id for brand in brands_id.value_ids},
                'weight': {weight.name: weight.id for weight in weights_id.value_ids},
                'purity': {purity.name: purity.id for purity in purities_id.value_ids},
            }

            bars_gold = self.env['product.template'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('name', '=', 'Bars Gold'),
            ], limit=1)
            if not bars_gold:
                bars_gold = bars_gold.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Bars Gold',
                    'categ_id': categ_bars.id,
                    'payment_page_ok': True,
                    'payment_price_flow': True,
                    'payment_price_method': 'formula',
                    'payment_color_foreground': '#000000',
                    'payment_color_background': '#F1C332',
                })
            bars_silver = self.env['product.template'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('name', '=', 'Bars Silver'),
            ], limit=1)
            if not bars_silver:
                bars_silver = bars_silver.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Bars Silver',
                    'categ_id': categ_bars.id,
                    'payment_page_ok': True,
                    'payment_price_flow': True,
                    'payment_price_method': 'formula',
                    'payment_color_foreground': '#000000',
                    'payment_color_background': '#F3F3F3',
                })
            base_gold = self.env['product.template'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('name', '=', 'Base Gold'),
            ], limit=1)
            if not base_gold:
                base_gold = base_gold.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Base Gold',
                    'default_code': 'XAUTRY',
                    'categ_id': categ_base_gold.id,
                    'payment_page_ok': True,
                    'payment_price_flow': True,
                    'payment_price_method': 'constant',
                    'payment_color_foreground': '#000000',
                    'payment_color_background': '#F1C332',
                })
            base_silver = self.env['product.template'].sudo().with_context(lang='en_US').search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
                ('name', '=', 'Base Silver'),
            ], limit=1)
            if not base_silver:
                base_silver = base_silver.create({
                    'system': 'jewelry',
                    'company_id': company.id,
                    'name': 'Base Silver',
                    'default_code': 'XAGTRY',
                    'categ_id': categ_base_silver.id,
                    'payment_page_ok': False,
                    'payment_price_flow': True,
                    'payment_price_method': 'constant',
                    'payment_color_foreground': '#000000',
                    'payment_color_background': '#F3F3F3',
                })

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
                    })] + [(0, 0, {
                        'attribute_id': purities_id.id,
                        'value_ids': [(4, attributes['purity'][name]) for name in types[prod['type']]['purity']]
                    })]
                    if prod['type'] == 'Bars':
                        attribute_line_ids.extend([(0, 0, {
                            'attribute_id': weights_id.id,
                            'value_ids': [(4, attributes['weight'][name]) for name in types[prod['type']]['weight']]
                        })])

                    values = {
                        'name': name,
                        'categ_id': categ.id,
                        'payment_price_flow': True,
                        'default_code': prod['code'],
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
                    ), (
                        attribute_purity_id and 1 or 0,
                        attribute_purity_id.id or 0,
                        {
                            'attribute_id': purities_id.id,
                            'value_ids': [(4, attributes['purity'][name]) for name in types[prod['type']]['purity']],
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
                        )])

                    values = {
                        'attribute_line_ids': attribute_line_ids,
                    }
                    if prod['type'] == 'Bars':
                        values['default_code'] = False
                    product.write(values)

            products = self.env['product.product'].sudo().with_context(lang='en_US', no_broadcast=True).search([
                ('system', '=', 'jewelry'),
                ('company_id', '=', company.id),
            ])
 
            attribute_keys = [] # It's used whether if same purity values occur
            for prod in prods:
                if prod['type'] == 'Bars':
                    product = products.filtered(lambda p: p.default_code == prod['code'])
                    values = {
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
                    values['payment_price_base'] = prod.get('base', 1)

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

                    # attribute_keys block begins
                    attribute_key = [template.id] + attribute_value_ids
                    if attribute_key in attribute_keys:
                        while True:
                            prod['purity'] += '0'
                            purity_id = attributes['purity'].get(prod['purity'])
                            if purity_id:
                                attributes['purity'][prod['purity']] = purity_id
                                attribute_value_ids[2] = purity_id
                                attribute_key[3] = purity_id
                                if attribute_key in attribute_keys:
                                    continue
                            else:
                                purities_name.append(prod['purity'])
                                purity = purities_id.value_ids.create({
                                    'attribute_id': purities_id.id,
                                    'name': prod['purity']
                                })
                                for bars in [bars_gold, bars_silver]:
                                    attribute_purity_id = bars.attribute_line_ids.filtered(lambda a: a.attribute_id.id == purities_id.id)
                                    bars.write({
                                        'attribute_line_ids': [(
                                            attribute_purity_id and 1 or 0, attribute_purity_id.id or 0,
                                            {'attribute_id': purities_id.id, 'value_ids': [(4, purity.id)]}
                                        )],
                                    })
                                
                                attributes['purity'][prod['purity']] = purity.id
                                attribute_value_ids[2] = purity.id
                                attribute_key[3] = purity.id
                            break
                    attribute_keys.append(attribute_key)
                    # attribute_keys block ends

                    attribute_values = self.env['product.template.attribute.value'].sudo().search([
                        ('attribute_id.system', '=', 'jewelry'),
                        ('attribute_id.company_id', '=', company.id),
                        ('product_tmpl_id', '=', template.id),
                        ('product_attribute_value_id', 'in', attribute_value_ids),
                    ])
                    values['product_template_attribute_value_ids'] = [(6, 0, attribute_values.ids)]

                    if product:
                        product.write(values)
                    else:
                        products.create({
                            'product_tmpl_id': template.id,
                            'default_code': prod['code'],
                            **values
                        })
                else:
                    product = products.filtered(lambda p: p.product_tmpl_id.default_code == prod['code'])
                    values = {
                        'payment_pid': prod['id'],
                        'payment_name': prod['name'],
                        'default_code': prod['code'],
                        'weight': float(prod['weight']),
                    }
                    if prod['metal'] == 'Gold':
                        values['payment_price_method_product_id'] = base_gold.id
                        values['payment_price_method_formula'] = 'x*%s' % prod.get('base', '1')
                    elif prod['metal'] == 'Silver':
                        values['payment_price_method_product_id'] = base_silver.id
                        values['payment_price_method_formula'] = 'x*%s' % prod.get('base', '1')
                    values['payment_price_base'] = prod.get('base', 1)

                    if product:
                        product.write(values)
                    else:
                        template = products_all.filtered(lambda p: p.default_code == prod['code'])

                        attribute_value_ids = [
                            attributes['brand'][prod['provider']],
                            attributes['purity'][prod['purity']],
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

            return {}
        return super().update_product()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    system = fields.Selection(selection_add=[('jewelry', 'Jewelry Payment System')])

    def get_payment_attribute(self, type=None):
        if self.env.company.system == 'jewelry':
            if type == 'brand':
                attributes = self.product_variant_ids.mapped('product_template_attribute_value_ids')

            lines = self.attribute_line_ids.filtered(lambda x: x.attribute_id.payment_type == type)
            result = []
            for line in lines:
                for value in line.value_ids:
                    if type == 'brand':
                        if attributes.filtered(lambda a: a.product_attribute_value_id.id == value.id).exists():
                            result.append({
                                'id': value.id,
                                'name': value.name,
                                'color': value.color,
                                'image': value.image_128 and value.image_128.decode('utf-8') or False,
                            })
            if not result:
                result.append({
                    'id': 0,
                    'name': '',
                    'color': '',
                    'image': False,
                })
            return result
        return super().get_payment_attribute(type=type)

    def get_payment_variants(self, types=None):
        if self.env.company.system == 'jewelry':
            result = {'': []}
            for variant in self.product_variant_ids:
                brand, weight, purity = '', 0, 0

                values = variant.product_template_attribute_value_ids.mapped('product_attribute_value_id')
                for value in values:
                    if value.attribute_id.payment_type == 'brand':
                        brand = value.id
                        if brand not in result:
                            result[brand] = []
                    elif value.attribute_id.payment_type == 'weight':
                        weight = value.name
                    elif value.attribute_id.payment_type == 'purity':
                        purity = value.name

                result[brand].append({
                    'id': variant.id,
                    'name': variant.name,
                    'price': variant.price or 0,
                    'currency': variant.currency_id,
                    'code': variant.default_code or '-',
                    'weight': weight or 0,
                    'purity': str(float(purity or 0))[1:],
                    'base': variant.payment_price_base,
                })
    
            for key, val in result.items():
                val.sort(key=lambda k: float(k['weight']))
            return result
        return super().get_payment_variants(types=types)


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
