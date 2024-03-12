# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PaymentSubscriptionLine(models.Model):
    _name = 'payment.subscription.line'
    _description = 'Payment Subscription Line'
    _check_company_auto = True

    @api.depends('price_unit', 'quantity', 'discount', 'subscription_id.pricelist_id', 'company_id')
    def _compute_price_subtotal(self):
        AccountTax = self.env['account.tax']
        for line in self:
            price = AccountTax._fix_tax_included_price_company(line.price_unit, line.product_id.sudo().taxes_id, AccountTax, line.company_id)
            line.price_subtotal = line.quantity * price * (100.0 - line.discount) / 100.0
            if line.subscription_id.pricelist_id.sudo().currency_id:
                line.price_subtotal = line.subscription_id.pricelist_id.sudo().currency_id.round(line.price_subtotal)

    subscription_id = fields.Many2one('payment.subscription', string='Subscription', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', check_company=True, domain="[('payment_recurring_invoice','=',True)]", required=True)
    company_id = fields.Many2one('res.company', related='subscription_id.company_id', store=True, index=True)
    name = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', help='Quantity that will be invoiced.', default=1.0, digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount')
    price_subtotal = fields.Float(compute='_compute_price_subtotal', string='Subtotal', digits='Account', store=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id
        partner = self.subscription_id.partner_id
        if partner.lang:
            product = product.with_context(lang=partner.lang)

        self.name = product.get_product_multiline_description_sale()
        self.uom_id = product.uom_id.id

    @api.onchange('product_id', 'quantity')
    def onchange_product_quantity(self):
        subscription = self.subscription_id
        company_id = subscription.company_id.id
        pricelist_id = subscription.pricelist_id.id
        context = dict(self.env.context, pricelist=pricelist_id,quantity=self.quantity)
        if not self.product_id:
            self.price_unit = 0.0
        else:
            partner = subscription.partner_id.with_company(company_id).with_context(context)
            if partner.lang:
                context.update({'lang': partner.lang})

            product = self.product_id.with_company(company_id).with_context(context)
            self.price_unit = product.price

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            if self.uom_id.id != product.uom_id.id:
                self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)

    @api.onchange('uom_id')
    def onchange_uom_id(self):
        if not self.uom_id:
            self.price_unit = 0.0
        else:
            return self.onchange_product_quantity()

    def get_template_option_line(self):
        if not self.subscription_id and not self.subscription_id.template_id:
            return False

        template = self.subscription_id.template_id
        return template.sudo().subscription_template_option_ids.filtered(lambda r: r.product_id == self.product_id)

    def _amount_line_tax(self):
        self.ensure_one()
        val = 0.0
        product = self.product_id
        product_tmp = product.sudo().product_tmpl_id
        for tax in product_tmp.taxes_id.filtered(lambda t: t.company_id == self.subscription_id.company_id):
            fpos_obj = self.env['account.fiscal.position']
            partner = self.subscription_id.partner_id
            fpos_id = fpos_obj.with_company(self.subscription_id.company_id.id).get_fiscal_position(partner.id)
            fpos = fpos_obj.browse(fpos_id)
            if fpos:
                tax = fpos.map_tax(tax, product, partner)
            compute_vals = tax.compute_all(self.price_unit * (1 - (self.discount or 0.0) / 100.0), self.subscription_id.currency_id, self.quantity, product, partner)['taxes']
            if compute_vals:
                val += compute_vals[0].get('amount', 0)
        return val

    @api.model
    def create(self, values):
        if values.get('product_id') and not values.get('name'):
            line = self.new(values)
            line.onchange_product_id()
            values['name'] = line._fields['name'].convert_to_write(line['name'], line)
        return super(PaymentSubscriptionLine, self).create(values)
