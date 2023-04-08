# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaymentItemWizard(models.TransientModel):
    _name = 'payment.item.wizard'
    _description = 'Payment Items Wizard'

    partner_id = fields.Many2one('res.partner', readonly=True)
    line_ids = fields.One2many('payment.item.wizard.line', 'wizard_id')

    def confirm(self):
        items = self.env['payment.item'].search([
            ('parent_id', '=', self.partner_id.id),
            ('paid', '=', False),
        ])
        item_ids = self.mapped('line_ids.item_id').ids
        for item in items:
            if item.id not in item_ids:
                item.unlink() 

        for line in self.line_ids:
            if line.item_id:
                if line.amount != line.item_id.amount:
                    line.item_id.amount = line.amount
            else:
                line.item_id = items.create({
                    'parent_id': self.partner_id.id,
                    'amount': line.amount,
                })
                line.item_id._onchange_parent_id()

        return {
            'name': 'Payment Items',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/p/%s' % self.partner_id._get_token()
        }


class PaymentItemWizardLine(models.TransientModel):
    _name = 'payment.item.wizard.line'
    _description = 'Payment Items Wizard Line'

    @api.depends('currency_id')
    def _compute_campaign(self):
        for line in self:
            line.campaign_id = line.item_id.campaign_id.id or line.wizard_id.partner_id.campaign_id.id

    wizard_id = fields.Many2one('payment.item.wizard')
    item_id = fields.Many2one('payment.item')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    campaign_id = fields.Many2one('payment.acquirer.jetcheckout.campaign', compute='_compute_campaign')
    paid = fields.Boolean(readonly=True)
    amount = fields.Monetary()
