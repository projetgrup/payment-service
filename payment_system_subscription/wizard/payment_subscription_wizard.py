# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PaymentSubscriptionWizard(models.TransientModel):
    _name = 'payment.subscription.wizard'
    _description = 'Subscription Upsell wizard'

    def _default_subscription(self):
        return self.env['payment.subscription'].browse(self._context.get('active_id'))

    subscription_id = fields.Many2one('payment.subscription', string='Subscription', required=True, default=_default_subscription, ondelete='cascade')
    option_lines = fields.One2many('payment.subscription.wizard.option', 'wizard_id', string='Options')
    date_from = fields.Date(
        string='Start Date',
        default=fields.Date.today,
        help='The discount applied when creating a sales order will be computed as the ratio between '
             'the full invoicing period of the subscription and the period between this date and the '
             'next invoicing date.'
    )

    def create_sale_order(self):
        fpos_id = self.env['account.fiscal.position'].with_company(self.subscription_id.company_id.id).get_fiscal_position(self.subscription_id.partner_id.id)
        sale_order_obj = self.env['sale.order']
        team = self.env['crm.team']._get_default_team_id(user_id=self.subscription_id.user_id.id)
        new_order_vals = {
            'partner_id': self.subscription_id.partner_id.id,
            'analytic_account_id': self.subscription_id.analytic_account_id.id,
            'team_id': team and team.id,
            'pricelist_id': self.subscription_id.pricelist_id.id,
            'fiscal_position_id': fpos_id,
            'payment_subscription_management': 'upsell',
            'origin': self.subscription_id.code,
            'company_id': self.subscription_id.company_id.id,
        }

        if self.subscription_id.partner_id.property_payment_term_id:
            new_order_vals['payment_term_id'] = self.subscription_id.partner_id.property_payment_term_id.id

        order = sale_order_obj.create(new_order_vals)
        order.message_post(body=(_('This upsell order has been created from the subscription ') + ' <a href=# data-oe-model=sale.subscription data-oe-id=%d>%s</a>' % (self.subscription_id.id, self.subscription_id.display_name)))
        for line in self.option_lines:
            self.subscription_id.partial_order_line(order, line, date_from=self.date_from)

        order.order_line._compute_tax_id()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'views': [[False, 'form']],
            'res_id': order.id,
        }


class PaymentSubscriptionWizardOption(models.TransientModel):
    _name = 'payment.subscription.wizard.option'
    _description = 'payment Subscription Upsell Lines Wizard'

    name = fields.Char(string='Description')
    wizard_id = fields.Many2one('payment.subscription.wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', required=True, domain="[('saas_recurring_invoice', '=', True)]", ondelete='cascade')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True, ondelete='cascade', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    quantity = fields.Float(default=1.0)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        else:
            self.name = self.product_id.get_product_multiline_description_sale()
            if not self.uom_id or self.product_id.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = self.product_id.uom_id.id
