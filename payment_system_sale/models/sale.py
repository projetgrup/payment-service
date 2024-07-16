# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _compute_transaction_count(self):
        for sale in self:
            sale.transaction_count = len(self.transaction_ids)

    def _compute_field_amount_approved(self):
        for sale in self:
            txs = sale.transaction_ids.filtered(lambda tx: tx.state == 'authorized')
            sale.field_amount_approved = txs.exists()


    system = fields.Selection(selection=[], readonly=True)
    amount_approved = fields.Float('Approved Amount')
    field_amount_approved = fields.Boolean(compute='_compute_field_amount_approved')
    transaction_count = fields.Integer(compute='_compute_transaction_count')

    @api.constrains('company_id', 'order_line')
    def _check_order_line_company_id(self):
        if self.system == 'oco':
            return
        return super()._check_order_line_company_id()

    @api.model_create_multi
    def create(self, vals_list):
        company = self.env.company
        if company.parent_id:
            company = company.parent_id
        if company.system:
            for vals in vals_list:
                vals['system'] = company.system
                #vals['company_id'] = company.id # It was closed because of OCO
        return super().create(vals_list)

    def action_view_transaction(self):
        transactions = self.mapped('transaction_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("payment.action_payment_transaction")
        if len(transactions) > 1:
            action['domain'] = [('id', 'in', transactions.ids)]
        elif len(transactions) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = transactions.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    paylox_system_price_unit = fields.Monetary()
    product_id = fields.Many2one('product.product', check_company=False)
