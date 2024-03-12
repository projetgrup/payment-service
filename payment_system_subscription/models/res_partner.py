# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_subscription_count(self):
        subs = self.env['payment.subscription'].sudo()
        for partner in self:
            partner.payment_subscription_count = subs.search_count([('partner_id', '=', partner.id)])

    payment_subscription_count = fields.Integer(string='Subscription Count', compute='_compute_subscription_count')
