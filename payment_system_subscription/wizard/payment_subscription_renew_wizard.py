# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PaymentSubscriptionWizard(models.TransientModel):
    _name = 'payment.subscription.renew.wizard'
    _description = 'Subscription Renew wizard'

    def _default_subscription(self):
        return self.env['payment.subscription'].browse(self._context.get('active_id'))

    def _default_products(self):
        self = self.with_context(active_test=False)
        payment_subscription_id = self.env['payment.subscription'].browse(self._context.get('active_id'))
        sub_default_products = payment_subscription_id.archived_product_ids
        res_ids = []
        options = self.env['payment.subscription.renew.wizard.option.keep']
        for product_id in sub_default_products:
            quantity = payment_subscription_id.recurring_invoice_line_ids.filtered(lambda p: p.product_id == product_id).mapped('quantity')

            value = {
                'name': product_id.name,
                'renew_product': True,
                'product_id': product_id.id,
                'quantity': quantity[0],
            }
            res_ids.append((0, 0, value))
            options |= options.new(value)
        return options

    payment_subscription_id = fields.Many2one('payment.subscription', string='Subscription', required=True, default=_default_subscription, ondelete='cascade')
    display_replacement_lines = fields.Boolean(compute='_compute_dismissed')
    kept_archived_product_ids = fields.One2many('payment.subscription.renew.wizard.option.keep', 'wizard_id', default=_default_products, string='Archived products', help='If checked, the product will be reused in the renewal order')
    replacement_line_ids = fields.One2many('payment.subscription.renew.wizard.option.replace', 'wizard_id', string='Replaced by')

    @api.depends('kept_archived_product_ids')
    def _compute_dismissed(self):
        for wizard in self:
            wizard.display_replacement_lines = wizard.payment_subscription_id.archived_product_count != sum(wizard.kept_archived_product_ids.mapped('renew_product'))

    def create_renewal_order(self):
        self = self.with_company(self.payment_subscription_id.company_id)
        not_renewed_products = self.kept_archived_product_ids.filtered(lambda rec: rec.renew_product is False)
        discard_ids = [x['product_id'] for x in not_renewed_products]
        return self.subscription_id.prepare_renewal_order(discard_product_ids=discard_ids, new_lines_ids=self.replacement_line_ids)


class PaymentSubscriptionRenewWizardOptionKeep(models.TransientModel):
    _name = 'payment.subscription.renew.wizard.option.keep'
    _description = 'payment Subscription Renew Lines Wizard'

    renew_product = fields.Boolean('Keep the product', default=True)
    name = fields.Char('Product')
    product_id = fields.Integer('id')
    quantity = fields.Integer()
    wizard_id = fields.Many2one('payment.subscription.renew.wizard', required=True, ondelete='cascade')


class PaymentSubscriptionRenewWizardOptionReplace(models.TransientModel):
    _name = 'payment.subscription.renew.wizard.option.replace'
    _description = 'Subscription Renew Lines Wizard'

    def _compute_product_attributes(self):
        for option in self:
            if option.product_id:
                option.name = option.product_id.get_product_multiline_description_sale()
                if not option.uom_id or option.product_id.uom_id.category_id.id != option.uom_id.category_id.id:
                    option.uom_id = option.product_id.uom_id.id

    wizard_id = fields.Many2one('payment.subscription.renew.wizard', required=True, ondelete='cascade')
    name = fields.Char(string='Description', compute='_compute_product_attributes')
    product_id = fields.Many2one('product.product', required=True, domain="[('payment_recurring_invoice', '=', True)]", ondelete='cascade')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, ondelete='cascade', domain="[('category_id', '=', product_uom_category_id)]", compute='_compute_product_attributes')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    quantity = fields.Float(default=1.0)
