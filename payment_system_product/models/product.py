# -*- coding: utf-8 -*-
import time
from psycopg2 import sql
from datetime import datetime

import odoo
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval

def _get_system(env):
    system = env.context.get('active_system') or env.context.get('system')
    company = env.company
    return system, company


class PaymentProduct(models.AbstractModel):
    _name = 'payment.product'
    _description = 'Payment System Product'

    @api.model
    def show_buttons(self):
        return {}

    @api.model
    def update_price(self):
        return False

    @api.model
    def get_price(self, products):
        company = self.env.company
        products = products.filtered(lambda p: p.company_id.id == company.id and p.system == company.system)
        return [(product.id, product.price) for product in products]

    @api.model
    def broadcast_price(self, products):
        if self.env.context.get('no_broadcast'):
            return

        prices = self.get_price(products)
        if prices:
            now = datetime.utcnow()
            pid = int(time.mktime(now.timetuple()))
            data = ['id:%s' % pid]
            for code, price in prices:
                data.append('data:%s;%s' % (code, price))

            @self.env.cr.postcommit.add
            def notify():
                with odoo.sql_db.db_connect('postgres').cursor() as cr:
                    query = sql.SQL("SELECT {}('sse', %s)").format(sql.Identifier('pg_notify'))
                    cr.execute(query, ('%s\n\n' % '\n'.join(data),))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('company_id')
    def _compute_price_flow(self):
        for product in self:
            product.payment_price_flow_option = 'dynamic' if product.payment_price_flow else 'static'

    def _set_price_flow(self):
        for product in self:
            product.payment_price_flow = product.payment_price_flow_option == 'dynamic'

    system = fields.Selection(selection=[], readonly=True)
    payment_page_ok = fields.Boolean()
    payment_color_foreground = fields.Char()
    payment_color_background = fields.Char()
    payment_price_flow = fields.Boolean()
    payment_price_flow_option = fields.Selection([
        ('static', 'Static'),
        ('dynamic', 'Dynamic'),
    ], compute='_compute_price_flow', inverse='_set_price_flow')
    payment_price_method = fields.Selection([
        ('constant', 'Constant'),
        ('formula', 'Formula'),
    ])
    payment_price_method_product_id = fields.Many2one('product.template')
    payment_price_method_formula = fields.Char()

    @api.model
    def _search(self, args, **kw):
        system, company = _get_system(self.env)
        if system:
            args += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            args += [('system', '=', False)]
        return super()._search(args, **kw)

    @api.model
    def _read_group_raw(self, domain, *args, **kwargs):
        system, company = _get_system(self.env)
        if system:
            domain += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            domain += [('system', '=', False)]
        return super()._read_group_raw(domain, *args, **kwargs)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        system, company = _get_system(self.env)
        if system:
            res['system'] = system
            res['company_id'] = company.id
            res['sale_ok'] = False
            res['purchase_ok'] = False
            res['detailed_type'] = 'service'
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system, company = _get_system(self.env)
        if system and view_type in ('form', 'tree', 'kanban', 'search'):
            view_id = self.env.ref('payment_system_product.%s_product_template' % (view_type,)).id
        return super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    def get_payment_attribute(self, type=None):
        lines = self.attribute_line_ids.filtered(lambda x: x.attribute_id.payment_type == type)
        result = []
        for line in lines:
            for value in line.value_ids:
                result.append({
                    'id': value.id,
                    'name': value.name,
                    'image': value.image_128 and value.image_128.decode('utf-8') or False,
                })
        return result

    def get_payment_variants(self, types=None):
        if not types:
            types = self.attribute_line_ids.mapped('attribute_id.payment_type')

        result = {}
        for variant in self.product_variant_ids:
            attrs = {type: 0 for type in types}
            values = variant.product_template_attribute_value_ids.mapped('product_attribute_value_id')
            for value in values:
                attrs[value.attribute_id.payment_type] = value.id

            key = []
            for type in types:
                key.append(attrs[type])

            result[tuple(key)] = {
                'id': variant.id,
                'name': variant.name,
                'price': variant.price or 0,
                'currency': variant.currency_id,
                'code': variant.default_code or '-',
            }
        return result

    def toggle_payment_page(self):
        self.payment_page_ok = not self.payment_page_ok


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('payment_price_method_product_id', 'payment_price_method_formula')
    def _compute_payment_price_method_result(self):
        for product in self:
            base = product.payment_price_method_product_id
            formula = product.payment_price_method_formula
            if base and formula:
                price = base.product_variant_ids[0].price
                formula = formula.replace('x', str(price))
                product.payment_price_method_result = safe_eval(formula)
            else:
                product.payment_price_method_result = 0

    price_dynamic = fields.Float('Price Dynamic', digits='Product Price')
    payment_price_method_product_id = fields.Many2one('product.template')
    payment_price_method_formula = fields.Char()
    payment_price_method_result = fields.Monetary(compute='_compute_payment_price_method_result')

    @api.model
    def _search(self, args, **kw):
        system, company = _get_system(self.env)
        if system:
            args += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            args += [('system', '=', False)]
        return super()._search(args, **kw)

    @api.model
    def _read_group_raw(self, domain, *args, **kwargs):
        system, company = _get_system(self.env)
        if system:
            domain += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            domain += [('system', '=', False)]
        return super()._read_group_raw(domain, *args, **kwargs)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system, company = _get_system(self.env)
        if system and view_type in ('form', 'tree', 'kanban', 'search'):
            view_id = self.env.ref('payment_system_product.%s_product_product' % (view_type,)).id
        return super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    def _compute_product_price(self):
        products = self.filtered(lambda p: p.payment_price_flow)
        for product in products:
            if product.payment_price_flow and product.payment_price_method == 'formula':
                product.price = product.payment_price_method_result
            elif len(product.product_tmpl_id.product_variant_ids) > 1:
                product.price = product.price_dynamic
            else:
                product.price = product.lst_price
        super(ProductProduct, self - products)._compute_product_price()

    def _set_product_price(self):
        products = self.filtered(lambda p: p.payment_price_flow)
        for product in products:
            if product.payment_price_flow and product.payment_price_method == 'formula':
                continue
            elif len(product.product_tmpl_id.product_variant_ids) > 1:
                product.price_dynamic = product.price
            else:
                product.lst_price = product.price
        super(ProductProduct, self - products)._set_product_price()

    def _broadcast_price(self, values={}):
        if 'price_dynamic' in values or 'payment_price_method_product_id' in values or 'payment_price_method_formula' in values:
            self.env['payment.product'].broadcast_price(self)
        elif 'base_unit_count' in values:
            products = self.search([('payment_price_method_product_id', 'in', self.mapped('product_tmpl_id').ids)])
            self.env['payment.product'].broadcast_price(products)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._broadcast_price()
        return res

    def write(self, values):
        res = super().write(values)
        self._broadcast_price(values)
        return res

    def unlink(self):
        self._broadcast_price()
        return super().unlink()


class ProductCategory(models.Model):
    _inherit = 'product.category'

    system = fields.Selection(selection=[], readonly=True)
    company_id = fields.Many2one('res.company')

    @api.model
    def _search(self, args, **kw):
        system, company = _get_system(self.env)
        if system:
            args += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            args += [('system', '=', False), ('company_id', '=', False)]
        return super()._search(args, **kw)

    @api.model
    def _read_group_raw(self, domain, *args, **kwargs):
        system, company = _get_system(self.env)
        if system:
            domain += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            domain += [('system', '=', False)]
        return super()._read_group_raw(domain, *args, **kwargs)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        system, company = _get_system(self.env)
        if system:
            res['system'] = system
            res['company_id'] = company.id
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system, company = _get_system(self.env)
        if system and view_type in ('form', 'tree', 'kanban', 'search'):
            view_id = self.env.ref('payment_system_product.%s_product_category' % (view_type,)).id
        return super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    system = fields.Selection(selection=[], readonly=True)
    company_id = fields.Many2one('res.company')
    payment_type = fields.Selection(selection=[('other', 'Other'), ('brand', 'Brand')], string='Type')

    @api.model
    def _search(self, args, **kw):
        system, company = _get_system(self.env)
        if system:
            args += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            args += [('system', '=', False), ('company_id', '=', False)]
        return super()._search(args, **kw)

    @api.model
    def _read_group_raw(self, domain, *args, **kwargs):
        system, company = _get_system(self.env)
        if system:
            domain += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            domain += [('system', '=', False)]
        return super()._read_group_raw(domain, *args, **kwargs)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        system, company = _get_system(self.env)
        if system:
            res['system'] = system
            res['company_id'] = company.id
            res['payment_type'] = 'other'
        return res

    @api.onchange('payment_type')
    def onchange_payment_type(self):
        if self.payment_type and self.payment_type != 'other':
            self.name = _(self.payment_type.capitalize())
        else:
            self.name = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        system, company = _get_system(self.env)
        if system and view_type in ('form', 'tree', 'kanban', 'search'):
            view_id = self.env.ref('payment_system_product.%s_product_attribute' % (view_type,)).id
        return super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)


class ProductAttributeValue(models.Model):
    _name = 'product.attribute.value'
    _inherit = ['product.attribute.value', 'image.mixin']

    system = fields.Selection(related='attribute_id.system', store=True)
    company_id = fields.Many2one(related='attribute_id.company_id', store=True)

    @api.model
    def _search(self, args, **kw):
        system, company = _get_system(self.env)
        if system:
            args += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            args += [('system', '=', False), ('company_id', '=', False)]
        return super()._search(args, **kw)

    @api.model
    def _read_group_raw(self, domain, *args, **kwargs):
        system, company = _get_system(self.env)
        if system:
            domain += [('system', '=', system), ('company_id', '=', company.id)]
        else:
            domain += [('system', '=', False)]
        return super()._read_group_raw(domain, *args, **kwargs)


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    product_attribute_value_color = fields.Integer(related='product_attribute_value_id.color')
